"""
FastAPI backend for Danny.

Run: uvicorn backend.app:app --reload
Docs: http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.models import TriageRequest, TriageResponse
from backend.triage import triage

app = FastAPI(
    title="Danny",
    description="AI-assisted IT helpdesk ticket triage with RAG-backed suggestions.",
    version="0.1.0",
)

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
    return triage(request.description)
