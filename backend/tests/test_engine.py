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
