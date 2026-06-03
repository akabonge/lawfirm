"""
Billie Jean Law — FastAPI application.
Serves the frontend and exposes the /api/chat endpoint for Vera.
"""
import re
import time
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import get_settings
from app.rag.ingest import ingest_knowledge_base
from app.rag.pipeline import generate_response
from app.tools.mock_db import init_db

app = FastAPI(title="Billie Jean Law — Vera AI Intake Specialist")

_frontend = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(_frontend / "static")), name="static")

# In-memory session history and rate-limit stores
_sessions: dict[str, list[dict]] = defaultdict(list)
_session_store: dict[str, list[float]] = defaultdict(list)
_ip_store: dict[str, list[float]] = defaultdict(list)

_INJECTION_PATTERNS = [
    r"ignore (all |previous |above )?instructions",
    r"(system|developer|assistant) (prompt|message|instructions)",
    r"jailbreak",
    r"forget (everything|all|your)",
    r"you are now",
    r"act as (if )?you",
    r"pretend (you are|to be)",
    r"disregard (your|all|previous)",
    r"new (instructions|persona|role|rules)",
    r"(reveal|show|print|output) (your |the )?(system |original )?prompt",
    r"<\s*(script|iframe|img|svg|object|embed|link)",
    r"javascript\s*:",
    r"on(load|click|error|mouseover)\s*=",
    r"(\bexec\b|\beval\b|\bimport\b.*\bos\b)",
    r"(\bsystem\b|\bsubprocess\b|\bshell\b)",
    r"--[a-z]",
    r"(union|select|insert|drop|delete|update)\s+(all\s+)?select",
    r"\x00|\x1a",
    r"(bypass|override|unlock|circumvent)",
    r"do anything now",
    r"dan mode",
    r"token\s*limit",
    r"prompt\s*injection",
]


def _is_injection(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in _INJECTION_PATTERNS)


@app.on_event("startup")
async def startup():
    init_db()
    ingest_knowledge_base()


@app.get("/")
async def index():
    return FileResponse(str(_frontend / "index.html"))


@app.get("/admin")
async def admin_page():
    return FileResponse(str(_frontend / "admin.html"))


@app.get("/api/admin/data")
async def admin_data(key: str = ""):
    import sqlite3
    from datetime import date as _date
    settings = get_settings()
    if key != settings.admin_key:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM consultations ORDER BY created_at DESC").fetchall()
    conn.close()
    today = _date.today().isoformat()
    data = [dict(r) for r in rows]
    return JSONResponse({
        "stats": {
            "total": len(data),
            "critical": sum(1 for r in data if r.get("urgency") == "critical"),
            "high": sum(1 for r in data if r.get("urgency") == "high"),
            "today": sum(1 for r in data if r.get("preferred_date") == today),
        },
        "consultations": data,
    })


class ChatRequest(BaseModel):
    message: str
    session_id: str


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request):
    if not req.message or not (1 <= len(req.message) <= 600):
        raise HTTPException(status_code=400, detail="Message must be 1–600 characters.")
    if not re.match(r"^[a-z0-9_]+$", req.session_id.lower()):
        raise HTTPException(status_code=400, detail="Invalid session ID.")
    if _is_injection(req.message):
        return JSONResponse({
            "response": "I can only help with legal intake and case questions for Billie Jean Law.",
            "sources": [],
        })

    now = time.time()

    # Session rate limit: 25 messages / 5 min
    sess_times = _session_store[req.session_id]
    sess_times[:] = [t for t in sess_times if now - t < 300]
    if len(sess_times) >= 25:
        return JSONResponse({
            "response": "You've reached the message limit for this session. Please call us at (540) 555-2400.",
            "sources": [],
        })
    sess_times.append(now)

    # IP rate limit: 120 req / hr
    ip = request.headers.get("X-Forwarded-For", "unknown").split(",")[0].strip()
    ip_times = _ip_store[ip]
    ip_times[:] = [t for t in ip_times if now - t < 3600]
    if len(ip_times) >= 120:
        return JSONResponse({
            "response": "Too many requests. Please call us directly at (540) 555-2400.",
            "sources": [],
        })
    ip_times.append(now)

    history = _sessions[req.session_id]
    response, sources, provider = generate_response(req.message, history)
    response = response[:2000]

    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": response})
    if len(history) > 20:
        _sessions[req.session_id] = history[-20:]

    return JSONResponse({"response": response, "sources": sources, "provider": provider})
