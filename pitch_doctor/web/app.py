"""FastAPI app: a reactive search bar that runs the same scan engine the CLI
uses and streams live progress while it works, then hands back the branded
report. No auth. An in-memory job dict is fine because uvicorn runs this as a
single process for local use.

The one thing this layer adds on top of the engine is lead capture: the form
requires a visitor's email before it will start a scan, and the resulting lead
is recorded in SQLite (see ``leads.py``). None of that reaches the engine --
the CLI still scans with no email anywhere in sight.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import re
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, field_validator, model_validator

from pitch_doctor.checks.runner import build_scan_context, run_all_checks
from pitch_doctor.cli import _format_date
from pitch_doctor.i18n import SUPPORTED_LANGUAGES, load_strings
from pitch_doctor.models import ScanReport
from pitch_doctor.report.builder import BrandInfo, write_report
from pitch_doctor.report.pdf_export import html_to_pdf
from pitch_doctor.scoring import score_and_grade
from pitch_doctor.web.leads import init_db, leads_path, save_lead
from pitch_doctor.web.templates import PAGE

# ---------------------------------------------------------------------------
# HMAC-signed URLs: prevents anyone from guessing report paths
# ---------------------------------------------------------------------------
# The signed filename embeds a HMAC-SHA256(token_hex + timestamp) so the
# browser receives a path like ``abc123<70-char-signature>.html`` that
# nobody can forge. The report is always written under the real filename,
# so we map signed → real via the HMAC.
_SIGN_SALT = os.environ.get("PITCH_DOCTOR_SIGN_SALT", "zerodigitx-2026")
_REPORT_TIMEOUT_SECONDS = 6 * 60 * 60  # signed links expire after 6 h

# ---------------------------------------------------------------------------
# Rate limiter: simple sliding-window per IP (in-memory, fine for single-process)
# ---------------------------------------------------------------------------
_RATE_LIMIT_MAX = 10  # scans per window
_RATE_LIMIT_WINDOW = 60  # seconds
_ip_timestamps: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    """Best-effort client IP. Behind Cloudflare the real IP is in CF-Connecting-IP."""
    return request.headers.get("cf-connecting-ip") or request.client.host if request.client else "0.0.0.0"


def _rate_limited(request: Request) -> bool:
    """Return True if the client has exceeded the rate limit."""
    ip = _client_ip(request)
    now = time.monotonic()
    window = _ip_timestamps[ip]
    cutoff = now - _RATE_LIMIT_WINDOW
    _ip_timestamps[ip] = [t for t in window if t > cutoff]
    if len(_ip_timestamps[ip]) >= _RATE_LIMIT_MAX:
        return True
    _ip_timestamps[ip].append(now)
    return False


# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------
_SAFE_FILENAME = re.compile(r"[A-Za-z0-9_.-]+\.html")
_SAFE_PDF_FILENAME = re.compile(r"[A-Za-z0-9_.-]+\.pdf")



def _encode_report_filename_v2(real_name: str) -> str:
    """Encode: ``real_name`` → ``real_name_<timestamp>_<sig>.html``."""
    ts = str(int(time.time()))
    name_without_ext, ext = os.path.splitext(real_name)
    clean = re.sub(r"[^A-Za-z0-9_-]", "_", name_without_ext)
    msg = f"{clean}:{ts}:{_SIGN_SALT}"
    sig = hmac.new(_SIGN_SALT.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return f"{clean}_{ts}_{sig[:32]}{ext}"


def _decode_report_filename_v2(signed_name: str) -> str | None:
    """Return the real filename if the signature is valid and not expired."""
    # Pattern: "<clean_stem>_<timestamp>_<32-hex-sig>.html"
    match = re.match(r"^([A-Za-z0-9_-]+)_(\d{10})_([a-f0-9]{32})(\.[^.]+)$", signed_name)
    if not match:
        return None
    stem, ts, sig, ext = match.groups()
    # Check expiration
    try:
        if time.time() - int(ts) > _REPORT_TIMEOUT_SECONDS:
            return None  # expired
    except ValueError:
        return None
    # Verify signature
    msg = f"{stem}:{ts}:{_SIGN_SALT}"
    expected = hmac.new(_SIGN_SALT.encode(), msg.encode(), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig, expected):
        return None
    return f"{stem}{ext}"


def _resolve_signed_report(out_dir: Path, signed_name: str) -> Path | None:
    """Map a signed URL filename to a file that actually exists.

    The public URL uses a sanitised stem (dots become underscores) plus HMAC.
    ``write_report`` still saves the original name (``example.com.html``), and
    the scan job also copies bytes to the signed name. Prefer the signed copy;
    fall back to the reconstructed stem, then to the unsanitised original if
    it is the only file on disk.
    """
    reconstructed = _decode_report_filename_v2(signed_name)
    if reconstructed is None:
        return None
    signed_path = out_dir / signed_name
    if signed_path.is_file():
        return signed_path
    reconstructed_path = out_dir / reconstructed
    if reconstructed_path.is_file():
        return reconstructed_path
    return None


# ---------------------------------------------------------------------------
# Every string the reactive UI needs, per language.
# ---------------------------------------------------------------------------
COPY: dict[str, dict] = {
    "en": {
        "heading": "Turn any bad website into your next client.",
        "subheading": "Scan and qualify prospects in 30 seconds.",
        "placeholder": "example.com",
        "cta": "Run diagnostic",
        "advanced_label": "Your information is required for your own site report",
        "lang_label": "Report language",
        "email_label": "Your email",
        "business_name_label": "Business name",
        "city_label": "City",
        "brand_name_label": "Your name",
        "brand_phone_label": "Contact phone",
        "contact_cta": "Update or build this site with a professional",
        "footer": "Public pages only. We store the lead next to the report — nothing is emailed automatically.",
        "scanning_label": "Scanning…",
        "error_heading": "Couldn't finish that scan",
        "need_target": "Enter a website URL, or a business name and city if there's no website.",
        "progress_note": "This usually takes 10–30 seconds.",
        "redirecting": "Done! Opening your report…",
        "kicker": "Digital presence diagnostic",
        "mode_site": "Has a website",
        "mode_none": "No website yet",
        "url_label": "Website to audit",
        "examples_label": "Try",
        "required_heading": "Where we send the report",
        "required_hint": "Required so we can attach the findings to you.",
        "step_of": "Step {current} of {total}",
        "elapsed": "{n}s elapsed",
        "privacy": "Privacy",
        "try_again": "Scan another",
        "field_email_error": "Enter a valid email.",
        "field_phone_error": "Enter a phone number we can call.",
        "field_name_error": "Enter your name.",
        "field_business_error": "Enter the business name.",
        "field_city_error": "Enter the city.",
        "stages": {
            "dns": "Checking DNS & reachability",
            "http": "Fetching the page & checking SSL",
            "browser": "Loading on mobile + desktop, capturing screenshots",
            "links": "Checking links & contact info",
            "presence": "Checking the Google listing & social profiles",
            "report": "Scoring and building your report",
        },
    },
    "es": {
        "heading": "Convierte cualquier sitio web deficiente en tu próximo cliente.",
        "subheading": "Escanea y califica prospectos en 30 segundos.",
        "placeholder": "ejemplo.com",
        "cta": "Correr diagnóstico",
        "advanced_label": "Tu información es necesaria para tu propio reporte del sitio",
        "lang_label": "Idioma del reporte",
        "email_label": "Tu correo",
        "business_name_label": "Nombre del negocio",
        "city_label": "Ciudad",
        "brand_name_label": "Tu nombre",
        "brand_phone_label": "Teléfono de contacto",
        "contact_cta": "Actualiza o crea este sitio de forma profesional",
        "footer": "Solo páginas públicas. Guardamos el lead junto al reporte — no enviamos el correo automáticamente.",
        "scanning_label": "Analizando…",
        "error_heading": "No se pudo completar el análisis",
        "need_target": "Escribe la URL del sitio web, o el nombre del negocio y la ciudad si no tiene sitio web.",
        "progress_note": "Esto suele tardar entre 10 y 30 segundos.",
        "redirecting": "¡Listo! Abriendo tu reporte…",
        "kicker": "Diagnóstico de presencia digital",
        "mode_site": "Tiene sitio web",
        "mode_none": "Aún no tiene sitio",
        "url_label": "Sitio a auditar",
        "examples_label": "Probar",
        "required_heading": "Dónde enviamos el reporte",
        "required_hint": "Necesario para asociar los hallazgos contigo.",
        "step_of": "Paso {current} de {total}",
        "elapsed": "{n}s transcurridos",
        "privacy": "Privacidad",
        "try_again": "Analizar otro",
        "field_email_error": "Escribe un correo válido.",
        "field_phone_error": "Escribe un teléfono al que podamos llamar.",
        "field_name_error": "Escribe tu nombre.",
        "field_business_error": "Escribe el nombre del negocio.",
        "field_city_error": "Escribe la ciudad.",
        "stages": {
            "dns": "Verificando DNS y accesibilidad",
            "http": "Descargando la página y revisando el SSL",
            "browser": "Cargando en móvil y escritorio, capturando pantallas",
            "links": "Revisando enlaces e información de contacto",
            "presence": "Revisando la ficha de Google y las redes sociales",
            "report": "Calculando el puntaje y generando tu reporte",
        },
    },
    "fr": {
        "heading": "Transformez n'importe quel site web bâclé en votre prochain client.",
        "subheading": "Analysez et qualifiez les prospects en 30 secondes.",
        "placeholder": "exemple.com",
        "cta": "Lancer le diagnostic",
        "advanced_label": "Vos informations sont nécessaires pour votre propre rapport du site",
        "lang_label": "Langue du rapport",
        "email_label": "Votre e-mail",
        "business_name_label": "Nom de l'entreprise",
        "city_label": "Ville",
        "brand_name_label": "Votre nom",
        "brand_phone_label": "Téléphone de contact",
        "contact_cta": "Mettez à jour ou créez ce site avec un professionnel",
        "footer": "Pages publiques uniquement. Le lead est stocké à côté du rapport — rien n'est envoyé automatiquement.",
        "scanning_label": "Analyse en cours…",
        "error_heading": "L'analyse n'a pas pu aboutir",
        "need_target": "Saisissez l'URL du site web, ou le nom de l'entreprise et la ville s'il n'y a pas de site.",
        "progress_note": "Cela prend généralement 10 à 30 secondes.",
        "redirecting": "Terminé ! Ouverture de votre rapport…",
        "kicker": "Diagnostic de présence digitale",
        "mode_site": "A un site web",
        "mode_none": "Pas encore de site",
        "url_label": "Site à auditer",
        "examples_label": "Essayer",
        "required_heading": "Où envoyer le rapport",
        "required_hint": "Nécessaire pour rattacher les constats à vous.",
        "step_of": "Étape {current} sur {total}",
        "elapsed": "{n}s écoulées",
        "privacy": "Confidentialité",
        "try_again": "Analyser un autre",
        "field_email_error": "Saisissez un e-mail valide.",
        "field_phone_error": "Saisissez un numéro joignable.",
        "field_name_error": "Saisissez votre nom.",
        "field_business_error": "Saisissez le nom de l'entreprise.",
        "field_city_error": "Saisissez la ville.",
        "stages": {
            "dns": "Vérification du DNS et de l'accessibilité",
            "http": "Récupération de la page et vérification du SSL",
            "browser": "Chargement mobile et bureau, capture des écrans",
            "links": "Vérification des liens et des coordonnées",
            "presence": "Vérification de la fiche Google et des réseaux sociaux",
            "report": "Calcul du score et génération du rapport",
        },
    },
}


class ScanRequest(BaseModel):
    """A scan started from the web form."""

    url: str | None = None
    business_name: str | None = None
    city: str | None = None
    email: str
    lang: str = "en"
    brand_name: str
    brand_email: str | None = None
    brand_phone: str

    @field_validator("url", "business_name", "city", mode="before")
    @classmethod
    def _blank_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("email")
    @classmethod
    def _valid_email(cls, value: str) -> str:
        value = value.strip()
        # Deliberately loose: this gates obvious junk, it isn't proof of deliverability.
        _EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")
        if not _EMAIL_RE.match(value):
            raise ValueError("a valid email address is required to generate a report")
        return value

    @model_validator(mode="after")
    def _needs_a_target(self) -> ScanRequest:
        if not self.url and not self.business_name:
            raise ValueError("provide a website URL, or a business name and city")
        if not self.url and not self.city:
            raise ValueError("a city is required when auditing a business with no website")
        return self


@dataclass
class Job:
    status: Literal["running", "done", "error"] = "running"
    stage: str = "dns"
    report_url: str | None = None
    error: str | None = None


def create_app(out_dir: Path, timeout: float = 25.0) -> FastAPI:
    # Use 25s timeout on Render so the first cold-start request has room to
    # complete before uvicorn kills it.  Local/dev can override via env.
    render_timeout = float(os.environ.get("PITCH_DOCTOR_RENDER_TIMEOUT", "25.0"))
    timeout = render_timeout if render_timeout > 0 else timeout

    app = FastAPI(
        title="pitch-doctor",
        docs_url=None,      # no /docs
        redoc_url=None,     # no /redoc
        openapi_url=None,   # no /openapi.json — kills the last public endpoint
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    init_db(leads_path(out_dir))
    jobs: dict[str, Job] = {}
    page_html = PAGE.replace("__COPY_JSON__", json.dumps(COPY))

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return page_html

    # ------------------------------------------------------------------
    # Health ping — Render free-plan sleeps after ~15 min; this ping
    # endpoint is hit by the Render uptime-checker to keep the container alive.
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Privacy policy page — bilingual (en/es)
    # ------------------------------------------------------------------
    _PRIVACY_DIR = Path(__file__).parent
    _PRIVACY_FILES = {
        "en": "privacy_en.html",
        "es": "privacy_es.html",
    }

    @app.get("/privacy")
    async def privacy_page(lang: str = "en"):
        _lang = lang if lang in _PRIVACY_FILES else "en"
        filename = _PRIVACY_FILES[_lang]
        path = _PRIVACY_DIR / filename
        if path.exists():
            return HTMLResponse(path.read_text(encoding="utf-8"))
        return HTMLResponse("Not found", status_code=404)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.post("/api/scan")
    async def start_scan(request: Request, req: ScanRequest):
        # Rate limit
        if _rate_limited(request):
            return JSONResponse(
                {"detail": "Too many scans — please wait a moment and try again."},
                status_code=429,
            )

        lang = req.lang if req.lang in SUPPORTED_LANGUAGES else "en"
        job_id = uuid.uuid4().hex
        jobs[job_id] = Job()

        async def run_job() -> None:
            job = jobs[job_id]
            try:
                strings = load_strings(lang)
                ctx = await build_scan_context(
                    req.url,
                    timeout=timeout,
                    on_progress=lambda stage: setattr(job, "stage", stage),
                    business_name=req.business_name,
                    city=req.city,
                )
                job.stage = "report"
                checks = run_all_checks(ctx, strings)
                score, grade = score_and_grade(checks)
                scan_report = ScanReport(
                    url=req.url,
                    lang=lang,
                    checks=checks,
                    score=score,
                    grade=grade,
                    mobile_screenshot_b64=ctx.mobile_screenshot_b64,
                    desktop_screenshot_b64=ctx.desktop_screenshot_b64,
                    scanned_at=_format_date(lang),
                    error=ctx.error,
                    business_name=ctx.business_name,
                    city=ctx.city,
                    has_website=ctx.has_website,
                )
                brand = BrandInfo(
                    name=req.brand_name or "Your Agency",
                    email=req.brand_email or req.email,
                    phone=req.brand_phone or "281-468-9892",
                )
                html_path = write_report(scan_report, strings, brand, out_dir)
                # Replace the public URL with an HMAC-signed variant
                signed_name = _encode_report_filename_v2(html_path.name)
                if html_path.name != signed_name:
                    (out_dir / signed_name).write_bytes(html_path.read_bytes())
                await asyncio.to_thread(
                    save_lead,
                    leads_path(out_dir),
                    email=req.email,
                    business_name=ctx.business_name,
                    city=ctx.city,
                    url=req.url,
                    score=score,
                )
                job.report_url = f"/reports/{signed_name}"
                job.status = "done"
            except Exception:  # noqa: BLE001
                # Surface to the client without leaking internal traces
                job.error = "scan failed — please try again"
                job.status = "error"

        asyncio.create_task(run_job())
        return {"job_id": job_id}

    @app.get("/api/status/{job_id}")
    async def status(job_id: str):
        job = jobs.get(job_id)
        if job is None:
            return JSONResponse({"status": "error", "error": "unknown job"}, status_code=404)
        return {
            "status": job.status,
            "stage": job.stage,
            "report_url": job.report_url,
            "error": job.error,
        }

    @app.get("/reports/{filename}", response_class=HTMLResponse)
    async def get_report(request: Request, filename: str):
        path = _resolve_signed_report(out_dir, filename)
        if path is None:
            return HTMLResponse("Not found", status_code=404)
        return HTMLResponse(path.read_text(encoding="utf-8"))

    @app.get("/pdf/{filename}")
    async def get_pdf(filename: str):
        """Serve existing PDF file — also requires valid HMAC."""
        # PDFs use the same naming scheme, but we decode the HTML signed name
        # and look for the corresponding .pdf.
        if not _SAFE_PDF_FILENAME.fullmatch(filename):
            return JSONResponse({"error": "Not found"}, status_code=404)
        path = _resolve_signed_report(out_dir, filename)
        if path is None:
            return JSONResponse({"error": "Not found"}, status_code=404)
        return FileResponse(
            path,
            media_type="application/pdf",
            filename=filename,
        )

    @app.post("/reports/{html_filename}/generate-pdf")
    async def generate_pdf(html_filename: str):
        """Generate PDF from HTML report — also requires valid HMAC."""
        if not _SAFE_FILENAME.fullmatch(html_filename):
            return JSONResponse({"error": "Invalid filename"}, status_code=400)
        html_path = _resolve_signed_report(out_dir, html_filename)
        if html_path is None:
            return JSONResponse({"error": "Report not found"}, status_code=404)

        pdf_filename = html_filename.replace(".html", ".pdf")
        pdf_path = out_dir / pdf_filename

        try:
            html_content = html_path.read_text(encoding="utf-8")
            success = html_to_pdf(html_content, pdf_path)
            if success and pdf_path.exists():
                return {
                    "status": "success",
                    "pdf_url": f"/pdf/{pdf_filename}",
                    "filename": pdf_filename,
                }
            else:
                return JSONResponse(
                    {"error": "PDF generation failed - weasyprint not available"},
                    status_code=500,
                )
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    return app
