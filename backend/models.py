from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


VerificationStatus = Literal["verified", "needs_review", "rejected"]


class Procedure(BaseModel):
    id: str
    label: str
    description: str
    synonyms: list[str]


class Facility(BaseModel):
    unique_id: str
    name: str
    state: str | None = None
    district: str | None = None
    city: str | None = None
    pincode: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    source_url: str | None = None
    specialties: list[str] = Field(default_factory=list)
    procedures: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    description: str | None = None
    last_updated: str | None = None
    human_verification_status: str = "unverified"
    human_verification_count: int = 0
    source_row: dict[str, Any] = Field(default_factory=dict)


class ScoreBreakdownItem(BaseModel):
    key: str
    label: str
    max_score: float
    score: float
    evidence: list[str] = Field(default_factory=list)


class FacilityScore(BaseModel):
    procedure: str
    total_score: float
    score_breakdown: list[ScoreBreakdownItem]
    uncertainty_flags: list[str]
    evidence_snippets: list[str]


class FacilityTopItem(Facility):
    score: float
    score_breakdown: list[ScoreBreakdownItem]
    uncertainty_flags: list[str]
    evidence_snippets: list[str]


class TrustCard(BaseModel):
    facility: Facility
    procedure: str
    score: float
    evidence_snippets: list[str]
    source_urls: list[str]
    uncertainty_flags: list[str]
    score_breakdown: list[ScoreBreakdownItem]
    human_verification_status: str
    human_verification_count: int
    verification_notes: list[str] = Field(default_factory=list)


class VerificationRequest(BaseModel):
    unique_id: str
    procedure: str
    status: VerificationStatus
    verifier_name: str | None = None
    notes: str | None = None
    evidence_url: str | None = None


class VerificationResponse(BaseModel):
    ok: bool
    verification_id: str
    facility: FacilityTopItem


class ShortlistRequest(BaseModel):
    unique_id: str
    procedure: str
    planner_name: str | None = None
    notes: str | None = None


class ShortlistResponse(BaseModel):
    ok: bool
    shortlist_id: str
    created_at: datetime


class AssistantQuery(BaseModel):
    question: str = Field(..., min_length=1)
    procedure: str | None = None
    state: str | None = None
    unique_id: str | None = None


class AssistantResponse(BaseModel):
    intent: str
    answer: str
    chart_type: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)
    uncertainty_flags: list[str] = Field(default_factory=list)


class VoiceRequest(BaseModel):
    transcript: str = Field(..., min_length=1)
    procedure: str | None = None
    unique_id: str | None = None
    session_id: str | None = None


class VoiceResponse(BaseModel):
    session_id: str
    text: str
    audio_url: str | None = None
    intent: str
    logged: bool
