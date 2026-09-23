from pydantic import BaseModel, Field


class TriageRequest(BaseModel):
    description: str = Field(..., min_length=5, max_length=2000)


class KBMatch(BaseModel):
    title: str
    category: str
    score: float
    body: str


class TriageResponse(BaseModel):
    predicted_category: str
    predicted_priority: str
    suggested_response: str
    kb_matches: list[KBMatch]
    mode: str  # "llm" or "rule_based_fallback"
