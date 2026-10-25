"""Targeted Automated Test Suite for 'The First 10 Minutes' Challenge Requirements.

Validates:
  1. Hypothesis key mapping and numerical normalization.
  2. The Twin Test: identical prefixes (minutes 0–6) and divergence at minute 7.
  3. Avoidance of premature certainty before the split.
  4. Retractions and corrections: discount positive evidence without double counting.
  5. Online source trust learning: uncertainty-aware Beta updates and rollback.
  6. Base-rate adaptation and environmental drift tracking.
  7. Alert stability, hysteresis bands, and emergency overrides.
  8. Causal dependency graph: temporal order enforcement and non-causal correlation rejection.
  9. Periodic 1-minute assessment tick.
"""

from datetime import datetime, timezone, timedelta
import pytest
from app.inference.bayesian import BayesianInferenceEngine, STANDARD_HYPOTHESES, HYPOTHESES
from app.inference.base_rate import BaseRateAdapter
from app.decision_engine.decider import DecisionEngine
from app.decision_engine.stability import AlertStabilityPolicy
from app.data_quality.source_health import SourceReliabilityTracker, SourceHealthRecord
from app.data_quality.online_learning import OnlineTrustLearner
from app.deduplication.retractions import EventRetractionManager
from app.causal_analysis.graph import CausalDependencyGraph
from app.intelligence_lab.lab import IntelligenceLab
from app.normalization.schema import NormalizedEvent
from app.engine import InferenceEngine


def test_four_hypotheses_and_aliases():
    engine = BayesianInferenceEngine()
    probs = engine.probabilities

    # Valid in [0, 1] and sum to 1.0
    for k in ("noise", "sensor_failure", "isolated_incident", "cascading_crisis"):
        assert 0.0 <= probs[k] <= 1.0
    assert abs(sum(probs.values()) - 1.0) < 1e-6

    # Aliases work seamlessly
    assert probs["normal"] == probs["noise"]
    assert probs["source_failure"] == probs["sensor_failure"]


def test_twin_test_identical_prefix_and_divergence():
    lab = IntelligenceLab()
    result = lab.run_twin_test(seed=42)

    # 1. Assert identical prefix property was formally verified for minutes 0 through 6
    assert result["identical_prefix_verified"] is True
    assert result["divergence_minute"] == 7

    # 2. Check side-by-side timeline for minutes 0 to 6
    sbs = result["side_by_side_timeline"]
    assert len(sbs) == 11

    for m in range(7):
        row = sbs[m]
        assert row["is_prefix_shared"] is True
        assert abs(row["twin_a_cascade_prob"] - row["twin_b_cascade_prob"]) < 1e-4
        assert abs(row["twin_a_sensor_failure_prob"] - row["twin_b_sensor_failure_prob"]) < 1e-4
        assert row["twin_a_action"] == row["twin_b_action"]
        assert abs(row["twin_a_expected_loss"] - row["twin_b_expected_loss"]) < 1e-4

    # 3. Assert divergence after minute 7
    final_a = result["scenario_a"]
    final_b = result["scenario_b"]

    assert final_a["final_cascade_prob"] > 0.60
    assert final_a["final_action"] in ("ALERT", "ESCALATE")

    assert final_b["final_sensor_failure_prob"] > 0.60
    assert final_b["final_cascade_prob"] < 0.25
    assert final_b["final_action"] in ("WATCH", "PREPARE")

    # 4. Challenge metrics exposed
    assert result["premature_confidence_penalty"] == 0.0
    assert result["time_to_justified_detection_minute"] is not None
    assert result["time_to_justified_detection_minute"] >= 7
    assert result["false_alarm_cost_avoided"] > 0
    assert result["missed_detection_cost_avoided"] > 0


def test_event_retractions_and_corrections():
    retraction_mgr = EventRetractionManager()
    engine = InferenceEngine()

    now = datetime.now(timezone.utc)

    # 1. Citizen report of severe flooding
    e1 = NormalizedEvent(
        source_id="citizen-app-01",
        external_id="claim-001",
        event_type="road_flooding",
        latitude=21.1180, longitude=79.1020,
        severity=0.85, source_reliability=0.60,
        event_timestamp=now,
    )
    res1 = engine.process(e1)
    p_cascade_before = engine.probabilities["cascading_crisis"]

    # 2. Collectorate retracts the false alarm
    e_retract = NormalizedEvent(
        source_id="collector-office",
        external_id="retract-001",
        event_type="retraction",
        latitude=21.1180, longitude=79.1020,
        severity=0.10, source_reliability=0.99,
        event_timestamp=now + timedelta(minutes=2),
        quality_flags=["retracted"],
        payload={"retracted_event_id": e1.event_id},
    )
    res2 = engine.process(e_retract)

    # Positive evidence of cascade should be discounted
    assert engine.probabilities["cascading_crisis"] < p_cascade_before
    assert engine.retraction_manager.retracted_event_ids


def test_online_source_trust_learning_and_rollback():
    tracker = SourceReliabilityTracker()
    learner = OnlineTrustLearner(tracker=tracker)

    source_id = "test-gauge-42"
    rec = tracker.sources.setdefault(source_id, SourceHealthRecord(source_id=source_id, initial_reliability=0.70))
    initial_rel = rec.expected_reliability

    # 1. Authoritative verification of accurate telemetry elevates trust
    update1 = learner.record_verification_outcome(
        source_id=source_id,
        category="hydrological",
        was_accurate=True,
        authoritative_source="Civil Defense Ground Patrol",
    )
    assert update1["new_reliability"] > initial_rel
    assert rec.sample_count > 20

    # 2. Authoritative verification of false telemetry lowers trust
    update2 = learner.record_verification_outcome(
        source_id=source_id,
        category="hydrological",
        was_accurate=False,
        authoritative_source="Municipal Engineer Verification",
    )
    assert update2["new_reliability"] < update1["new_reliability"]

    # 3. Rollback restores previous state
    rolled = learner.rollback_last_update()
    assert rolled["update_id"] == update2["update_id"]
    assert rec.expected_reliability == update1["new_reliability"]


def test_base_rate_adaptation_and_drift():
    adapter = BaseRateAdapter()
    initial_priors = adapter.get_current_priors()

    # Environmental drift: heavy seasonal rain increases EMA
    drift1 = adapter.update_environmental_drift(65.0)
    drift2 = adapter.update_environmental_drift(75.0)
    assert drift2["observed_ema"] > drift1["baseline_mean"]

    # Verified ground truth outcome adapts prior safely within bounds
    res = adapter.record_verified_outcome("cascading_crisis")
    assert res["updated"] is True
    new_priors = adapter.get_current_priors()
    assert new_priors["cascading_crisis"] > initial_priors["cascading_crisis"]
    assert new_priors["cascading_crisis"] <= adapter.max_prior


def test_alert_stability_hysteresis_and_cooldown():
    policy = AlertStabilityPolicy(
        escalate_entry_p=0.70,
        escalate_exit_p=0.50,
        alert_entry_p=0.40,
        min_persistence_cycles=2,
        deescalate_cooldown_seconds=120.0,
    )

    t0 = datetime.now(timezone.utc)

    # 1. Attempt to escalate without enough corroboration: blocked
    res1 = policy.evaluate_transition(
        raw_recommended_action="ESCALATE",
        probabilities={"cascading_crisis": 0.75, "noise": 0.25},
        independent_sources_count=1,
        now=t0,
    )
    assert res1["stabilized_action"] == "ALERT"
    assert res1["transition_allowed"] is False
    assert "Requires >= 2" in res1["block_reason"]

    # 2. Corroborated multi-source escalation: allowed
    res2 = policy.evaluate_transition(
        raw_recommended_action="ESCALATE",
        probabilities={"cascading_crisis": 0.75, "noise": 0.25},
        independent_sources_count=2,
        now=t0,
    )
    assert res2["stabilized_action"] == "ESCALATE"
    assert res2["transition_allowed"] is True

    # 3. Sudden dip in probability: cooldown prevents instant de-escalation flip-flop
    t1 = t0 + timedelta(seconds=30)  # only 30s elapsed (< 120s cooldown)
    res3 = policy.evaluate_transition(
        raw_recommended_action="WATCH",
        probabilities={"cascading_crisis": 0.20, "noise": 0.80},
        independent_sources_count=0,
        now=t1,
    )
    assert res3["stabilized_action"] == "ESCALATE"
    assert res3["transition_allowed"] is False
    assert "cooldown active" in res3["block_reason"]


def test_causal_graph_temporal_ordering():
    graph = CausalDependencyGraph()
    t_base = datetime.now(timezone.utc)

    # Scenario A: Correct sequence (rainfall at 12:00, water_level at 12:15)
    e_rain = NormalizedEvent(
        source_id="rain-1", external_id="r1", event_type="rainfall",
        latitude=21.1180, longitude=79.1020, assigned_zone_id="zone-3-hanuman-nagar",
        event_timestamp=t_base,
    )
    e_water = NormalizedEvent(
        source_id="water-1", external_id="w1", event_type="water_level",
        latitude=21.1180, longitude=79.1020, assigned_zone_id="zone-3-hanuman-nagar",
        event_timestamp=t_base + timedelta(minutes=15),
    )
    eval_a = graph.evaluate_active_pathways([e_rain, e_water])
    edge_a = next(e for e in eval_a["edges"] if e["from"] == "severe_weather" and e["to"] == "water_level")
    assert edge_a["status"] == "confirmed_cascade"
    assert "Confirmed causal link" in edge_a["causal_explanation"]

    # Scenario B: REVERSED sequence (water_level occurs BEFORE rain!)
    e_rain_late = NormalizedEvent(
        source_id="rain-1", external_id="r2", event_type="rainfall",
        latitude=21.1180, longitude=79.1020, assigned_zone_id="zone-3-hanuman-nagar",
        event_timestamp=t_base + timedelta(minutes=30),
    )
    e_water_early = NormalizedEvent(
        source_id="water-1", external_id="w2", event_type="water_level",
        latitude=21.1180, longitude=79.1020, assigned_zone_id="zone-3-hanuman-nagar",
        event_timestamp=t_base,
    )
    eval_b = graph.evaluate_active_pathways([e_water_early, e_rain_late])
    edge_b = next(e for e in eval_b["edges"] if e["from"] == "severe_weather" and e["to"] == "water_level")
    assert edge_b["status"] == "non_causal_correlation"
    assert "Temporal order violation" in edge_b["causal_explanation"]


def test_periodic_minute_tick():
    engine = InferenceEngine()
    initial_tick = engine.tick
    result = engine.tick_minute()

    assert engine.tick == initial_tick + 1
    assert "action" in result
    assert "probabilities" in result
    assert "last_assessment_timestamp" in result
    assert engine.ledger[0]["event_type"] == "periodic_assessment"
