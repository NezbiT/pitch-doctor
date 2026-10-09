"""
CRM API para leads de pitch-doctor.

Lee leads.db (SQLite) y expone un endpoint REST para el dashboard.
Se instala en zerodigitx.com como ruta /api/crm/leads.

Uso:
1. Instalar en el server de zerodigitx.com
2. Configurar PITCH_DOCTOR_DB para apuntar a leads.db
3. El frontend accede a /api/crm/leads

Para usar sin cambiar zerodigitx.com, ejecutar standalone:
  python crm-lead-api.py --port 8001
"""

from __future__ import annotations

import csv
import io
import json
import sqlite3
import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="CRM Lead API — pitch-doctor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to zerodigitx.com domain
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Path to leads.db — override with env var
LEADS_DB = Path(__file__).parent / "leads.db"


def get_db() -> sqlite3.Connection:
    """Get database connection, creating table if needed."""
    conn = sqlite3.connect(str(LEADS_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT NOT NULL,
            business_name TEXT,
            city          TEXT,
            url           TEXT,
            score         INTEGER,
            created_at    TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


class Lead(BaseModel):
    id: Optional[int] = None
    email: str
    business_name: Optional[str] = None
    city: Optional[str] = None
    url: Optional[str] = None
    score: Optional[int] = None
    created_at: Optional[str] = None


@app.get("/crm/leads")
async def get_leads(
    search: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    score_min: Optional[int] = Query(None),
    date_range: Optional[int] = Query(None),  # days
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Get filtered leads with pagination."""
    db = get_db()
    try:
        query = "SELECT * FROM leads WHERE 1=1"
        params = {}
        
        if search:
            query += " AND (email LIKE :search OR business_name LIKE :search OR city LIKE :search)"
            params["search"] = f"%{search}%"
        
        if city:
            query += " AND city = :city"
            params["city"] = city
        
        if score_min is not None:
            query += " AND score >= :score_min"
            params["score_min"] = score_min
        
        if date_range:
            cutoff = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=date_range)).isoformat()
            query += " AND created_at >= :cutoff"
            params["cutoff"] = cutoff
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        total = db.execute(count_query, params).fetchone()[0]
        
        # Paginate
        offset = (page - 1) * page_size
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = page_size
        params["offset"] = offset
        
        rows = db.execute(query, params).fetchall()
        leads = [dict(row) for row in rows]
        
        return {
            "leads": leads,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }
    finally:
        db.close()


@app.get("/crm/leads/stats")
async def get_stats():
    """Get summary statistics."""
    db = get_db()
    try:
        total = db.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        
        avg_score_row = db.execute(
            "SELECT AVG(score) as avg_score FROM leads WHERE score IS NOT NULL"
        ).fetchone()
        avg_score = round(avg_score_row["avg_score"]) if avg_score_row["avg_score"] else None
        
        new_this_month = db.execute(
            "SELECT COUNT(*) FROM leads WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
        ).fetchone()[0]
        
        top_cities = db.execute(
            "SELECT city, COUNT(*) as count FROM leads WHERE city IS NOT NULL GROUP BY city ORDER BY count DESC LIMIT 5"
        ).fetchall()
        
        return {
            "total": total,
            "avg_score": avg_score,
            "new_this_month": new_this_month,
            "top_cities": [dict(c) for c in top_cities],
        }
    finally:
        db.close()


@app.get("/crm/leads/export")
async def export_leads(
    search: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    score_min: Optional[int] = Query(None),
    date_range: Optional[int] = Query(None),
):
    """Export filtered leads as CSV."""
    db = get_db()
    try:
        query = "SELECT * FROM leads WHERE 1=1"
        params = {}
        
        if search:
            query += " AND (email LIKE :search OR business_name LIKE :search OR city LIKE :search)"
            params["search"] = f"%{search}%"
        
        if city:
            query += " AND city = :city"
            params["city"] = city
        
        if score_min is not None:
            query += " AND score >= :score_min"
            params["score_min"] = score_min
        
        if date_range:
            cutoff = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=date_range)).isoformat()
            query += " AND created_at >= :cutoff"
            params["cutoff"] = cutoff
        
        query += " ORDER BY created_at DESC"
        
        rows = db.execute(query, params).fetchall()
        
        # Build CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["email", "business_name", "city", "url", "score", "created_at"])
        for row in rows:
            writer.writerow([row["email"], row["business_name"], row["city"], row["url"], row["score"], row["created_at"]])
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=leads-pitch-doctor-{datetime.date.today()}.csv"},
        )
    finally:
        db.close()


@app.post("/crm/leads")
async def create_lead(lead: Lead):
    """Create a new lead (for testing/development)."""
    db = get_db()
    try:
        now = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
        cursor = db.execute(
            "INSERT INTO leads (email, business_name, city, url, score, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (lead.email, lead.business_name, lead.city, lead.url, lead.score, now)
        )
        db.commit()
        return {"id": cursor.lastrowid, "status": "created"}
    finally:
        db.close()


@app.get("/health")
async def health():
    """Health check."""
    db_path = Path(LEADS_DB)
    exists = db_path.exists()
    size = db_path.stat().st_size if exists else 0
    return {
        "status": "ok",
        "db_exists": exists,
        "db_size_mb": round(size / (1024 * 1024), 2),
    }


# Standalone mode for quick testing
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CRM Lead API — pitch-doctor leads viewer")
    parser.add_argument("--port", type=int, default=8001, help="Port to run on")
    parser.add_argument("--db", type=str, default=None, help="Path to leads.db")
    args = parser.parse_args()
    
    if args.db:
        LEADS_DB = Path(args.db)
    
    print(f"Starting CRM Lead API on port {args.port}")
    print(f"Database: {LEADS_DB}")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=args.port)
