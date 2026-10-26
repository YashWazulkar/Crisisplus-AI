from datetime import datetime, timedelta, timezone

from app.engine import InferenceEngine, HYPOTHESES
from app.schemas import Event

def test_probabilities_sum_to_one():
    engine = InferenceEngine()
    event = Event(event_id="test-1", event_type="road_flooding", source_id="road-1",
                  reliability=.95, severity=.9)
    engine.process(event)
    assert abs(sum(engine.probabilities.values()) - 1.0) < 1e-9
    assert set(engine.probabilities) == set(HYPOTHESES)

def test_duplicate_does_not_update_belief():
    engine = InferenceEngine()
    event = Event(event_id="duplicate-1", event_type="road_flooding", source_id="road-1",
                  reliability=.95, severity=.9)
    engine.process(event)
    first = engine.probabilities.copy()
    result = engine.process(event)
    assert result["accepted"] is False
    assert engine.probabilities == first

def test_source_failure_is_evidence_for_failure_hypothesis():
    engine = InferenceEngine()
    event = Event(event_id="failure-1", event_type="gateway_failure", source_id="gateway-controller",
                  gateway_id="water-gw", reliability=.98, severity=.95)
    engine.process(event)
    assert engine.probabilities["source_failure"] > engine.priors["source_failure"]

def test_assessment_updates_response_and_snapshots_do_not_advance_hysteresis():
    engine = InferenceEngine()
    engine.probabilities = {
        "normal": 0.05,
        "source_failure": 0.02,
        "isolated_incident": 0.03,
        "cascading_crisis": 0.90,
    }

    assessment = engine.tick_minute()
    assert assessment["action"] == "ALERT"
    assert engine.snapshot()["action"] == assessment["action"]

    stable_cycle_count = engine.decision_engine.stability_policy.consecutive_count
    engine.snapshot()
    engine.snapshot()
    assert engine.decision_engine.stability_policy.consecutive_count == stable_cycle_count

    engine.decision_engine.stability_policy.last_transition_time = (
        datetime.now(timezone.utc) - timedelta(minutes=5)
    )
    engine.probabilities = {
        "normal": 0.95,
        "source_failure": 0.02,
        "isolated_incident": 0.02,
        "cascading_crisis": 0.01,
    }

    engine.tick_minute()
    assessment = engine.tick_minute()
    assert assessment["action"] == "WATCH"
    assert engine.snapshot()["action"] == "WATCH"

def test_area_response_uses_local_evidence_instead_of_district_action():
    engine = InferenceEngine()
    area_id = "zone-1-laxmi-nagar"
    untouched_area_id = "zone-8-lakadganj"
    untouched_prior = engine.zone_bayesian[untouched_area_id].probabilities

    result = engine.process(Event(
        event_id="laxmi-road-flooding",
        event_type="road_flooding",
        source_id="laxmi-field-team",
        latitude=21.1150,
        longitude=79.0600,
        severity=0.95,
        reliability=0.99,
    ))

    snapshot = engine.snapshot()
    assert result["accepted"] is True
    assert snapshot["active_zone_id"] == area_id
    assert snapshot["subregions"][area_id]["event_count"] == 1
    assert snapshot["subregions"][area_id]["action"] == "ALERT"
    assert snapshot["subregions"][area_id]["decision_reasons"]
    assert snapshot["subregions"][area_id]["supporting_evidence"]
    assert snapshot["subregions"][area_id]["probabilities"] != untouched_prior
    assert snapshot["subregions"][untouched_area_id]["action"] == "WATCH"
    assert "no recent local observations" in snapshot["subregions"][untouched_area_id]["decision_reasons"]
    assert snapshot["risk_overview"]["risk_area_id"] == area_id
    assert snapshot["risk_overview"]["most_affected_area"] == snapshot["subregions"][area_id]["name"]
    assert set(snapshot["risk_overview"]["response_rationales"]) == {
        "WATCH", "PREPARE", "ALERT", "ESCALATE"
    }
    assert "at least 2 independent verified source groups" in snapshot["risk_overview"]["response_rationales"]["ESCALATE"]
    assert snapshot["risk_overview"]["expected_costs"] == snapshot["subregions"][area_id]["expected_costs"]
    assert snapshot["subregions"][untouched_area_id]["probabilities"] == untouched_prior

    engine.zone_norm_events[area_id][0].ingestion_timestamp = (
        datetime.now(timezone.utc) - timedelta(minutes=11)
    )
    engine.tick_minute()
    assert engine.snapshot()["subregions"][area_id]["action"] == "WATCH"
