"""
FastAPI backend for DeskOracle.

Run: uvicorn backend.app:app --reload
Docs: http://127.0.0.1:8000/docs
"""
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models import TriageRequest, TriageResponse
from backend.triage import triage

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DeskOracle",
    description="AI-assisted IT helpdesk ticket triage with RAG-backed suggestions.",
    version="0.1.0",
)

# Wide open for local/demo use. Scope allow_origins to a real allowlist
# before deploying this behind a public URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/tickets/triage", response_model=TriageResponse)
def triage_ticket(request: TriageRequest) -> TriageResponse:
    try:
        return triage(request.description)
    except Exception:
        logger.exception("Unhandled error while triaging ticket")
        raise HTTPException(status_code=500, detail="Failed to triage ticket")
