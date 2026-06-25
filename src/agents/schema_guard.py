from pydantic import BaseModel, Field


class RemedyOutputSchema(BaseModel):
    condition_confirmed: str = Field(description="Ayurvedic taxonomy matching the condition")
    formulation_name: str = Field(description="Name of the traditional formulation")
    source_citation: str = Field(description="Exact reference: Grantha, Sthana, Chapter, Verse")
    modern_evidence_summary: str = Field(description="Summary of verified clinical research")
    duration_days: int = Field(description="Target implementation timeframe", ge=1, le=365)


class QueryResponseSchema(BaseModel):
    answer: str
    remedies: list[RemedyOutputSchema] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    grounded: bool = True
    safety_notes: list[str] = Field(default_factory=list)
    query_intent: str = ""
    conditions_detected: list[str] = Field(default_factory=list)
    query: str = ""
    sources_used: int = 0
