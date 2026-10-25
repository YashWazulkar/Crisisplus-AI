"""Unit Tests for xAI Integration, Grounding Validation, and Fallback."""

import pytest
from app.xai.models import EvidencePacket, ObservationEvidence, XAIExplanationResponse
from app.xai.validator import XAIGroundingValidator
from app.xai.client import XAIClient

def make_sample_packet(action="PREPARE") -> EvidencePacket:
    obs = [
        ObservationEvidence(
            source_id="imd-rmc-nagpur",
            event_type="severe_weather",
            title="IMD Nagpur Warning: Moderate Rain & Thunderstorms (Yellow)",
            severity=0.45,
            confidence=0.90,
            data_provenance="LIVE",
            geographic_precision="district_level",
            assigned_zone_name="Nagpur District",
            timestamp_utc="2026-10-25T12:00:00Z",
            age_seconds=120.0,
            quality_flags=["imd_color_yellow"],
        ),
        ObservationEvidence(
            source_id="open-meteo-nagpur",
            event_type="rainfall",
            title="Precipitation: 28.5 mm/h (Nagpur)",
            magnitude=28.5,
            magnitude_unit="mm/h",
            severity=0.62,
            confidence=0.88,
            data_provenance="LIVE",
            geographic_precision="district_level",
            assigned_zone_name="Nagpur District",
            timestamp_utc="2026-10-25T12:01:00Z",
            age_seconds=60.0,
        ),
    ]

    return EvidencePacket(
        packet_id="packet-test-01",
        timestamp_utc="2026-10-25T12:02:00Z",
        target_region="Nagpur District",
        target_zone_id="zone-2-dharampeth",
        target_zone_name="Dharampeth Zone",
        authoritative_action=action,
        probabilities={"normal": 0.20, "source_failure": 0.10, "isolated_incident": 0.35, "cascading_crisis": 0.35},
        dominant_hypothesis="isolated_incident",
        expected_costs={"WATCH": 6.5, "PREPARE": 3.8, "ALERT": 4.2, "ESCALATE": 8.0},
        supporting_observations=obs,
        contradictory_observations=[],
        missing_data_gaps=["Municipal stormwater IoT level sensors awaiting token"],
        active_corroborated_sources_count=2,
        data_quality_factor=0.85,
    )

def test_deterministic_explanation_synthesis():
    client = XAIClient()
    packet = make_sample_packet(action="PREPARE")
    explanation = client.generate_deterministic_explanation(packet)

    assert isinstance(explanation, XAIExplanationResponse)
    assert explanation.affected_region == "Dharampeth Zone"
    assert "PREPARE" in explanation.decision_rationale
    assert "imd-rmc-nagpur" in explanation.evidence_synthesis
    assert "open-meteo-nagpur" in explanation.evidence_synthesis
    assert len(explanation.recommended_verification_steps) >= 3
    assert explanation.provider_status == "deterministic_fallback"
    assert explanation.grounding_verified is True

def test_grounding_validator_prevents_override():
    packet = make_sample_packet(action="PREPARE")
    # Simulate an LLM output that tried to claim ESCALATE
    raw_llm_output = {
        "summary": "Immediate disaster mobilization required.",
        "hazard_assessment": "Severe flash flood.",
        "affected_region": "Nagpur District",
        "evidence_synthesis": "Heavy rain observed.",
        "contradictory_evidence_analysis": "None",
        "missing_data_disclosure": "None",
        "decision_rationale": "I recommend ESCALATE immediately.",
        "recommended_verification_steps": ["Call emergency services"],
        "uncertainty_level": "Low",
    }

    validated = XAIGroundingValidator.validate_and_repair(raw_llm_output, packet, model_name="grok-2-1212")

    # Must retain authoritative action PREPARE
    assert "Authoritative Recommendation: PREPARE" in validated.decision_rationale
    assert validated.grounding_verified is True

def test_xai_client_fallback_when_unconfigured():
    client = XAIClient()
    client.api_key = ""
    packet = make_sample_packet(action="WATCH")

    coro = client.explain_assessment(packet)
    try:
        coro.send(None)
    except StopIteration as e:
        res = e.value
    assert res.provider_status in ("deterministic_fallback", "cached")
    assert "WATCH" in res.decision_rationale
    assert "Dharampeth Zone" in res.affected_region
