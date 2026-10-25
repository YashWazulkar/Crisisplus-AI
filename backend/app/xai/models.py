"""xAI Data Schemas and Structured Evidence Packet Models for Nagpur CrisisPulse."""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field


class ObservationEvidence(BaseModel):
    """An individual verified observation included in the analytical evidence packet."""
    source_id: str
    event_type: str
    title: str
    magnitude: float | None = None
    magnitude_unit: str | None = None
    severity: float
    confidence: float
    data_provenance: str = "LIVE"
    geographic_precision: str = "approximate"
    assigned_zone_name: str | None = None
    timestamp_utc: str
    age_seconds: float
    quality_flags: list[str] = Field(default_factory=list)


class EvidencePacket(BaseModel):
    """Authoritative analytical evidence packet assembled by backend inference engine."""
    packet_id: str
    timestamp_utc: str
    target_region: str
    target_zone_id: str | None = None
    target_zone_name: str | None = None
    authoritative_action: Literal["WATCH", "PREPARE", "ALERT", "ESCALATE"]
    probabilities: dict[str, float]
    dominant_hypothesis: str
    expected_costs: dict[str, float]
    supporting_observations: list[ObservationEvidence]
    contradictory_observations: list[str] = Field(default_factory=list)
    missing_data_gaps: list[str] = Field(default_factory=list)
    active_corroborated_sources_count: int
    data_quality_factor: float
    forecast_summary: str | None = None


class XAIExplanationResponse(BaseModel):
    """Structured, evidence-grounded explanation produced by xAI (Grok) or deterministic fallback."""
    summary: str = Field(..., description="One sentence operational assessment")
    hazard_assessment: str = Field(..., description="Description of the emerging physical hazard")
    affected_region: str = Field(..., description="Specific Nagpur zone or district area affected")
    evidence_synthesis: str = Field(..., description="Direct synthesis of cited supporting observations and timestamps")
    contradictory_evidence_analysis: str = Field(..., description="Analysis of conflicting or unverified reports")
    missing_data_disclosure: str = Field(..., description="Explicit disclosure of missing sensor feeds or telemetry gaps")
    decision_rationale: str = Field(..., description="Why the system recommended WATCH, PREPARE, ALERT, or ESCALATE")
    recommended_verification_steps: list[str] = Field(..., description="Actions responders must verify next")
    uncertainty_level: Literal["Low", "Moderate", "High"] = Field(..., description="Overall model uncertainty")
    provider_status: Literal["xai_grok_live", "deterministic_fallback", "cached"] = Field(...)
    model_identifier: str
    grounding_verified: bool = Field(default=True)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
