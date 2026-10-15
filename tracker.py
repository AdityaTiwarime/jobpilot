import json
import os
from datetime import datetime

from sqlalchemy import create_engine, text

# Local runs use a SQLite file; on the cloud set DATABASE_URL (Neon Postgres) so data survives restarts
DB_URL = os.getenv("DATABASE_URL", "sqlite:///jobs.db").strip()
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DB_URL, pool_pre_ping=True)

with engine.begin() as con:
    con.execute(text("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY, title TEXT, company TEXT, location TEXT, url TEXT,
            description TEXT, source TEXT, ats TEXT, score INTEGER,
            matched TEXT, missing TEXT, status TEXT DEFAULT 'new',
            found_at TEXT, applied_at TEXT, notes TEXT DEFAULT ''
        )"""))
    con.execute(text("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)"))


def save(jobs):
    now = datetime.now().isoformat(timespec="minutes")
    added = 0
    with engine.begin() as con:
        for j in jobs:
            res = con.execute(text("""
                INSERT INTO jobs (id, title, company, location, url, description,
                    source, ats, score, matched, missing, found_at)
                VALUES (:id, :title, :company, :location, :url, :description,
                    :source, :ats, :score, :matched, :missing, :found_at)
                ON CONFLICT (id) DO NOTHING"""),
                {**j, "matched": json.dumps(j["matched"]), "missing": json.dumps(j["missing"]),
                 "found_at": now})
            added += res.rowcount
    return added


def jobs(status=None, min_score=0):
    sql = "SELECT * FROM jobs WHERE score >= :min"
    args = {"min": min_score}
    if status:
        sql += " AND status = :status"
        args["status"] = status
    with engine.connect() as con:
        rows = con.execute(text(sql + " ORDER BY score DESC, found_at DESC"), args).mappings().all()
    return [dict(r) for r in rows]


def get(job_id):
    with engine.connect() as con:
        row = con.execute(text("SELECT * FROM jobs WHERE id = :id"), {"id": job_id}).mappings().first()
    return dict(row) if row else None


def set_status(job_id, status):
    applied = datetime.now().isoformat(timespec="minutes") if status == "applied" else None
    with engine.begin() as con:
        con.execute(text("UPDATE jobs SET status = :s, applied_at = COALESCE(:a, applied_at) WHERE id = :id"),
                    {"s": status, "a": applied, "id": job_id})


def stats():
    with engine.connect() as con:
        rows = con.execute(text("SELECT status, COUNT(*) AS n FROM jobs GROUP BY status")).all()
    return {r[0]: r[1] for r in rows}


def get_setting(key, default=None):
    with engine.connect() as con:
        row = con.execute(text("SELECT value FROM settings WHERE key = :k"), {"k": key}).first()
    return row[0] if row else default


def set_setting(key, value):
    with engine.begin() as con:
        con.execute(text("""INSERT INTO settings (key, value) VALUES (:k, :v)
                            ON CONFLICT (key) DO UPDATE SET value = excluded.value"""),
                    {"k": key, "v": value})
