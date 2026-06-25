from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    user_id: Optional[str] = None
    season: Optional[str] = None


class ProfileRequest(BaseModel):
    user_id: Optional[str] = None
    prakriti: Dict = Field(default_factory=dict)
    vikriti: Dict = Field(default_factory=dict)
    allergies: List[str] = Field(default_factory=list)
    contraindications: List[str] = Field(default_factory=list)
    active_protocol: Dict = Field(default_factory=dict)


class FeedbackRequest(BaseModel):
    user_id: str
    formulation_name: str
    outcome: str = Field(pattern="^(helped|no_effect|worsened)$")
    checkpoint_day: int = Field(ge=1, le=365)
    notes: str = ""


class ProgressFailureRequest(BaseModel):
    user_id: str
    current_protocol_id: str
    observed_imbalance: str


class IngestVerseRequest(BaseModel):
    text: str
    grantha: str
    sthana: str
    adhyaya: int
    shloka: int
    language: str = "san"
    metadata: Dict = Field(default_factory=dict)
