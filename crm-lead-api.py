"""
CRM API para leads de pitch-doctor.

Expone en solo lectura la tabla ``leads`` que llena el formulario web
(``<out>/leads.db``: ``reports/leads.db`` por defecto, ``/app/reports/leads.db``
en Docker).

Configuración (variables de entorno):
  CRM_API_TOKEN        Obligatorio. Toda petición a /crm/* debe enviar
                       ``Authorization: Bearer <token>``; sin token configurado
                       la API responde 503 en vez de abrirse.
  PITCH_DOCTOR_DB      Ruta a leads.db (por defecto reports/leads.db).
  CRM_ALLOWED_ORIGINS  Orígenes CORS separados por coma
                       (por defecto https://zerodigitx.com).

Uso standalone:
  CRM_API_TOKEN=... python crm-lead-api.py --port 8001 [--db reports/leads.db] [--host 127.0.0.1]
"""

from __future__ import annotations

import csv
import datetime
import io
import os
import secrets
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pitch_doctor.web.leads import leads_path

DEFAULT_ORIGINS = "https://zerodigitx.com"
CSV_COLUMNS = ("email", "business_name", "city", "url", "score", "created_at")
# Cells starting with these are evaluated as formulas by Excel/Sheets. Lead
# fields come from a public form, so the export must neutralise them.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

_bearer = HTTPBearer(auto_error=False)


def require_token(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> None:
    expected = os.environ.get("CRM_API_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="CRM_API_TOKEN is not configured")
    if creds is None or not secrets.compare_digest(
        creds.credentials.encode(), expected.encode()
    ):
        raise HTTPException(
            status_code=401,
            detail="invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def db_path() -> Path:
    return Path(os.environ.get("PITCH_DOCTOR_DB") or leads_path(Path("reports")))


@contextmanager
def open_db() -> Iterator[sqlite3.Connection]:
    """Read-only connection: this API never writes to the lead store."""
    path = db_path()
    if not path.exists():
        raise HTTPException(status_code=503, detail="leads database not found")
    conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def build_filters(
    search: str | None,
    city: str | None,
    score_min: int | None,
    date_range: int | None,
) -> tuple[str, dict[str, Any]]:
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if search:
        clauses.append("(email LIKE :search OR business_name LIKE :search OR city LIKE :search)")
        params["search"] = f"%{search}%"
    if city:
        clauses.append("city = :city")
        params["city"] = city
    if score_min is not None:
        clauses.append("score >= :score_min")
        params["score_min"] = score_min
    if date_range:
        cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=date_range)
        clauses.append("created_at >= :cutoff")
        params["cutoff"] = cutoff.isoformat(timespec="seconds")
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params


def csv_cell(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


router = APIRouter(prefix="/crm", dependencies=[Depends(require_token)])


@router.get("/leads")
async def get_leads(
    search: Annotated[str | None, Query()] = None,
    city: Annotated[str | None, Query()] = None,
    score_min: Annotated[int | None, Query()] = None,
    date_range: Annotated[int | None, Query()] = None,  # days
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
):
    """Get filtered leads with pagination."""
    where, params = build_filters(search, city, score_min, date_range)
    with open_db() as db:
        total = db.execute(f"SELECT COUNT(*) FROM leads{where}", params).fetchone()[0]
        rows = db.execute(
            f"SELECT * FROM leads{where} ORDER BY created_at DESC LIMIT :limit OFFSET :offset",
            {**params, "limit": page_size, "offset": (page - 1) * page_size},
        ).fetchall()
    return {
        "leads": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/leads/stats")
async def get_stats():
    """Get summary statistics."""
    with open_db() as db:
        total = db.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        avg_score = db.execute(
            "SELECT AVG(score) FROM leads WHERE score IS NOT NULL"
        ).fetchone()[0]
        new_this_month = db.execute(
            "SELECT COUNT(*) FROM leads"
            " WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
        ).fetchone()[0]
        top_cities = db.execute(
            "SELECT city, COUNT(*) AS count FROM leads WHERE city IS NOT NULL"
            " GROUP BY city ORDER BY count DESC LIMIT 5"
        ).fetchall()
    return {
        "total": total,
        "avg_score": round(avg_score) if avg_score is not None else None,
        "new_this_month": new_this_month,
        "top_cities": [dict(c) for c in top_cities],
    }


@router.get("/leads/export")
async def export_leads(
    search: Annotated[str | None, Query()] = None,
    city: Annotated[str | None, Query()] = None,
    score_min: Annotated[int | None, Query()] = None,
    date_range: Annotated[int | None, Query()] = None,
):
    """Export filtered leads as CSV."""
    where, params = build_filters(search, city, score_min, date_range)
    with open_db() as db:
        rows = db.execute(
            f"SELECT {', '.join(CSV_COLUMNS)} FROM leads{where} ORDER BY created_at DESC",
            params,
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_COLUMNS)
    for row in rows:
        writer.writerow([csv_cell(row[col]) for col in CSV_COLUMNS])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=leads-pitch-doctor-{datetime.date.today()}.csv"
        },
    )


app = FastAPI(title="CRM Lead API — pitch-doctor")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip()
        for o in os.environ.get("CRM_ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",")
        if o.strip()
    ],
    allow_methods=["GET"],
    allow_headers=["Authorization"],
)
app.include_router(router)


@app.get("/health")
async def health():
    """Liveness probe; reveals nothing about the leads."""
    return {"status": "ok"}


if __name__ == "__main__":
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="CRM Lead API — pitch-doctor leads viewer")
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind (default: localhost only)")
    parser.add_argument("--port", type=int, default=8001, help="Port to run on")
    parser.add_argument("--db", default=None, help="Path to leads.db (overrides PITCH_DOCTOR_DB)")
    args = parser.parse_args()

    if not os.environ.get("CRM_API_TOKEN"):
        parser.error("CRM_API_TOKEN must be set; refusing to serve leads without auth")
    if args.db:
        os.environ["PITCH_DOCTOR_DB"] = args.db

    print(f"Starting CRM Lead API on {args.host}:{args.port}")
    print(f"Database: {db_path()}")
    uvicorn.run(app, host=args.host, port=args.port)
