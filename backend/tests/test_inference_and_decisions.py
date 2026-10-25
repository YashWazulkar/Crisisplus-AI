"""Tests for Bayesian Belief Updates, Anomaly Detection, and Decision Engine."""

from app.normalization.schema import NormalizedEvent
from app.inference.bayesian import BayesianInferenceEngine
from app.inference.anomaly_detector import AnomalyDetector
from app.decision_engine.decider import DecisionEngine

def test_bayesian_updates_and_tempering():
    engine = BayesianInferenceEngine()
    prior = engine.probabilities.copy()

    # Severe earthquake observation
    event = NormalizedEvent(
        source_id="usgs-earthquake",
        external_id="eq-001",
        event_type="earthquake",
        latitude=35.0,
        longitude=-118.0,
        severity=0.85,
        source_reliability=0.98,
    )
    prior_out, post_out = engine.update(event, quality_weight=0.95)

    assert post_out["cascading_crisis"] > prior["cascading_crisis"]
    assert abs(sum(post_out.values()) - 1.0) < 1e-9

def test_anomaly_detector_mad_robust_z():
    detector = AnomalyDetector()

    # Feed baseline rainfall of 2-5 mm/h
    for val in [2.0, 3.1, 2.5, 4.0, 2.8, 3.5, 3.0, 2.9, 4.2, 3.2]:
        evt = NormalizedEvent(
            source_id="rain-gauge",
            external_id=f"base-{val}",
            event_type="rainfall",
            latitude=19.0,
            longitude=72.8,
            magnitude=val,
            severity=0.2,
        )
        anomalies = detector.evaluate(evt)
        rain_anomalies = [a for a in anomalies if a.metric_name == "precipitation_burst"]
        assert len(rain_anomalies) == 0

    # Sudden burst of 55 mm/h
    burst_evt = NormalizedEvent(
        source_id="rain-gauge",
        external_id="burst-01",
        event_type="rainfall",
        latitude=19.0,
        longitude=72.8,
        magnitude=55.0,
        severity=0.95,
    )
    burst_anomalies = detector.evaluate(burst_evt)
    assert len(burst_anomalies) >= 1
    assert burst_anomalies[0].is_anomaly is True
    assert burst_anomalies[0].score >= 3.0

def test_decision_engine_cautious_escalation_gate():
    decider = DecisionEngine(escalation_threshold=0.70)

    # If cascading probability is high (0.80) but only ONE source exists,
    # the cautious gate should prevent ESCALATE and cap recommendation at ALERT.
    single_source_event = [
        NormalizedEvent(
            source_id="only-source-1",
            external_id="e-1",
            event_type="road_flooding",
            latitude=19.0,
            longitude=72.8,
            severity=0.9,
        )
    ]
    high_cascade_prob = {"normal": 0.05, "source_failure": 0.05, "isolated_incident": 0.10, "cascading_crisis": 0.80}

    decision = decider.evaluate(high_cascade_prob, single_source_event)
    assert decision["raw_cost_optimal_action"] == "ESCALATE"
    assert decision["action"] == "ALERT"  # Gated to ALERT due to lack of multi-source corroboration!
    assert "at least 2 independent verified sources" in decision["gate_reason"]

    # Now add an independent second source
    two_source_events = single_source_event + [
        NormalizedEvent(
            source_id="independent-source-2",
            external_id="e-2",
            event_type="water_level",
            latitude=19.05,
            longitude=72.85,
            severity=0.88,
        )
    ]
    corroborated_decision = decider.evaluate(high_cascade_prob, two_source_events)
    assert corroborated_decision["action"] == "ESCALATE"  # Gate opens!
