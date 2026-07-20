"""FastAPI app: a reactive search bar that runs the same scan engine the CLI
uses and streams live progress while it works, then hands back the branded
report. Local-only tool: no auth, no database. An in-memory job dict is fine
because uvicorn runs this as a single process for local use.
"""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from pitch_doctor.checks.runner import build_scan_context, run_all_checks
from pitch_doctor.cli import _format_date
from pitch_doctor.i18n import SUPPORTED_LANGUAGES, load_strings
from pitch_doctor.models import ScanReport
from pitch_doctor.report.builder import BrandInfo, write_report
from pitch_doctor.scoring import score_and_grade
from pitch_doctor.web.templates import PAGE

_SAFE_FILENAME = re.compile(r"[A-Za-z0-9_.-]+\.html")

# Every string the reactive UI needs, per language. Kept separate from
# pitch_doctor/i18n/*.json (which is the *report's* content contract) since
# this is UI chrome for an optional add-on surface, not the deliverable.
COPY: dict[str, dict] = {
    "en": {
        "heading": "Turn any bad website into your next client.",
        "subheading": "Scan and qualify prospects in 30 seconds.",
        "placeholder": "example.com",
        "cta": "Scan",
        "advanced_label": "Your information",
        "lang_label": "Report language",
        "brand_name_label": "Your name",
        "brand_email_label": "Contact email",
        "brand_phone_label": "Contact phone",
        "contact_cta": "Update or Create Your Website Professionally",
        "footer": "Runs locally. Reports are saved to disk, same as the CLI.",
        "scanning_label": "Scanning…",
        "error_heading": "Couldn't finish that scan",
        "progress_note": "This usually takes 10-30 seconds.",
        "redirecting": "Done! Opening your report…",
        "stages": {
            "dns": "Checking DNS & reachability",
            "http": "Fetching the page & checking SSL",
            "browser": "Loading on mobile + desktop, capturing screenshots",
            "links": "Checking links & contact info",
            "report": "Scoring and building your report",
        },
    },
    "es": {
        "heading": "Convierte cualquier sitio web deficiente en tu próximo cliente.",
        "subheading": "Escanea y califica prospectos en 30 segundos.",
        "placeholder": "ejemplo.com",
        "cta": "Analizar",
        "advanced_label": "Tu información",
        "lang_label": "Idioma del reporte",
        "brand_name_label": "Tu nombre",
        "brand_email_label": "Correo de contacto",
        "brand_phone_label": "Teléfono de contacto",
        "contact_cta": "Actualiza o Crea Tu Sitio Web de Forma Profesional",
        "footer": "Corre localmente. Los reportes se guardan en disco, igual que la CLI.",
        "scanning_label": "Analizando…",
        "error_heading": "No se pudo completar el análisis",
        "progress_note": "Esto suele tardar entre 10 y 30 segundos.",
        "redirecting": "¡Listo! Abriendo tu reporte…",
        "stages": {
            "dns": "Verificando DNS y accesibilidad",
            "http": "Descargando la página y revisando el SSL",
            "browser": "Cargando en móvil y escritorio, capturando pantallas",
            "links": "Revisando enlaces e información de contacto",
            "report": "Calculando el puntaje y generando tu reporte",
        },
    },
    "fr": {
        "heading": "Transformez n'importe quel site web bâclé en votre prochain client.",
        "subheading": "Analysez et qualifiez les prospects en 30 secondes.",
        "placeholder": "exemple.com",
        "cta": "Analyser",
        "advanced_label": "Vos informations",
        "lang_label": "Langue du rapport",
        "brand_name_label": "Votre nom",
        "brand_email_label": "E-mail de contact",
        "brand_phone_label": "Téléphone de contact",
        "contact_cta": "Mettez à Jour ou Créez Votre Site Web de Manière Professionnelle",
        "footer": "Fonctionne localement. Les rapports sont enregistrés sur disque, comme avec la CLI.",
        "scanning_label": "Analyse en cours…",
        "error_heading": "L'analyse n'a pas pu aboutir",
        "progress_note": "Cela prend généralement 10 à 30 secondes.",
        "redirecting": "Terminé ! Ouverture de votre rapport…",
        "stages": {
            "dns": "Vérification du DNS et de l'accessibilité",
            "http": "Récupération de la page et vérification du SSL",
            "browser": "Chargement mobile et bureau, capture des écrans",
            "links": "Vérification des liens et des coordonnées",
            "report": "Calcul du score et génération du rapport",
        },
    },
}


class ScanRequest(BaseModel):
    url: str
    lang: str = "en"
    brand_name: str
    brand_email: str
    brand_phone: str


@dataclass
class Job:
    status: Literal["running", "done", "error"] = "running"
    stage: str = "dns"
    report_url: str | None = None
    error: str | None = None


def create_app(out_dir: Path, timeout: float = 25.0) -> FastAPI:
    app = FastAPI(title="pitch-doctor", docs_url=None, redoc_url=None)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs: dict[str, Job] = {}
    page_html = PAGE.replace("__COPY_JSON__", json.dumps(COPY))

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return page_html

    @app.post("/api/scan")
    async def start_scan(req: ScanRequest):
        lang = req.lang if req.lang in SUPPORTED_LANGUAGES else "en"
        job_id = uuid.uuid4().hex
        jobs[job_id] = Job()

        async def run_job() -> None:
            job = jobs[job_id]
            try:
                strings = load_strings(lang)
                ctx = await build_scan_context(
                    req.url, timeout=timeout, on_progress=lambda stage: setattr(job, "stage", stage)
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
                )
                brand = BrandInfo(
                    name=req.brand_name or "Your Agency",
                    email=req.brand_email or None,
                    phone=req.brand_phone or None,
                )
                html_path = write_report(scan_report, strings, brand, out_dir)
                job.report_url = f"/reports/{html_path.name}"
                job.status = "done"
            except Exception as exc:  # noqa: BLE001 -- surface any failure to the polling client
                job.error = str(exc)
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
    async def get_report(filename: str):
        if not _SAFE_FILENAME.fullmatch(filename):
            return HTMLResponse("Not found", status_code=404)
        path = out_dir / filename
        if not path.exists():
            return HTMLResponse("Not found", status_code=404)
        return HTMLResponse(path.read_text(encoding="utf-8"))

    return app
