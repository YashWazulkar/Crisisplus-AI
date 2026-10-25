"""Tests for the First-10-Minute Intelligence Lab and Evaluation Module."""

from app.intelligence_lab.lab import IntelligenceLab
from app.evaluation.evaluator import ModelEvaluator

def test_intelligence_lab_minute_by_minute_replay():
    lab = IntelligenceLab()
    replay = lab.replay_sequence("cascade", seed=42)

    assert replay["scenario"] == "cascade"
    assert len(replay["timeline"]) == 11  # Minute 0 to 10
    minute_0 = replay["timeline"][0]
    minute_10 = replay["timeline"][10]

    assert minute_0["minute"] == 0
    assert minute_10["minute"] == 10
    # In genuine cascade, cascade belief should be substantially higher at minute 10 than at minute 0
    assert minute_10["probabilities"]["cascading_crisis"] > minute_0["probabilities"]["cascading_crisis"]
    assert "missing_information_needed" in minute_10

def test_intelligence_lab_twin_test_divergence():
    lab = IntelligenceLab()
    twin_res = lab.run_twin_test(seed=42)

    assert twin_res["divergence_minute"] == 7
    twin_a = twin_res["scenario_a"]
    twin_b = twin_res["scenario_b"]

    # At minute 6, both twins must have identical cascade probabilities
    prob_a_min6 = twin_a["timeline"][6]["probabilities"]["cascading_crisis"]
    prob_b_min6 = twin_b["timeline"][6]["probabilities"]["cascading_crisis"]
    assert abs(prob_a_min6 - prob_b_min6) < 1e-4

    # At minute 10, Twin A escalates into crisis while Twin B detects source failure
    assert twin_a["final_cascade_prob"] > 0.60
    assert twin_b["final_cascade_prob"] < 0.30
    assert twin_b["timeline"][10]["probabilities"]["source_failure"] > 0.40

def test_intelligence_lab_counterfactual_analysis():
    lab = IntelligenceLab()
    base_probs = {"normal": 0.40, "source_failure": 0.15, "isolated_incident": 0.25, "cascading_crisis": 0.20}

    # What if cloudburst rainfall spikes?
    cf = lab.run_counterfactual(base_probs, counterfactual_type="rainfall_spikes")
    assert cf["is_hypothetical"] is True
    assert cf["delta_cascade_prob"] > 0.0

def test_model_evaluation_metrics():
    evaluator = ModelEvaluator()
    report = evaluator.run_benchmark_evaluation(runs_per_scenario=2)

    assert "metrics" in report
    m = report["metrics"]
    assert 0.0 <= m["precision"] <= 1.0
    assert 0.0 <= m["recall"] <= 1.0
    assert 0.0 <= m["f1_score"] <= 1.0
    assert 0.0 <= m["brier_score"] <= 1.0
    assert m["average_lead_time_minutes"] >= 0.0
    assert report["sample_scenario_runs"] > 0
