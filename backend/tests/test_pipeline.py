"""Tests for Validation, Deduplication, and Data Quality Pipeline."""

from datetime import datetime, timezone, timedelta
from app.normalization.schema import NormalizedEvent
from app.validation.validator import EventValidator
from app.deduplication.deduplicator import EventDeduplicator
from app.data_quality.scorer import DataQualityScorer

def test_validation_bounds_checking():
    # Valid event
    valid_evt = NormalizedEvent(
        source_id="open-meteo",
        external_id="test-valid-01",
        event_type="rainfall",
        latitude=19.076,
        longitude=72.877,
        severity=0.6,
    )
    res = EventValidator.validate(valid_evt)
    assert res.is_valid is True

    # Invalid latitude caught by Pydantic bounds
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        NormalizedEvent(
            source_id="open-meteo",
            external_id="test-inv-lat",
            event_type="rainfall",
            latitude=95.0,  # Invalid
            longitude=72.877,
            severity=0.5,
        )

    # Invalid future timestamp beyond clock skew
    future_evt = NormalizedEvent(
        source_id="usgs-earthquake",
        external_id="test-future",
        event_type="earthquake",
        latitude=35.0,
        longitude=-120.0,
        event_timestamp=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    res = EventValidator.validate(future_evt)
    assert res.is_valid is False
    assert "future" in res.rejection_reason

def test_deduplicator_exact_and_spatiotemporal():
    dedup = EventDeduplicator(spatial_window_km=10.0, time_window_seconds=600.0)

    now = datetime.now(timezone.utc)
    evt1 = NormalizedEvent(
        event_id="evt-uniq-1",
        source_id="usgs",
        external_id="usgs-1234",
        event_type="earthquake",
        latitude=37.77,
        longitude=-122.41,
        event_timestamp=now,
        severity=0.5,
    )

    # First event accepted
    res1 = dedup.check_and_register(evt1)
    assert res1.is_duplicate is False

    # Exact duplicate rejected
    res2 = dedup.check_and_register(evt1)
    assert res2.is_duplicate is True

    # Spatio-temporal duplicate (same place, 2 minutes later, same source and type)
    evt3 = NormalizedEvent(
        event_id="evt-uniq-2",
        source_id="usgs",
        external_id="usgs-different-ext",
        event_type="earthquake",
        latitude=37.78,  # ~1.1km away
        longitude=-122.41,
        event_timestamp=now + timedelta(minutes=2),
        severity=0.51,  # near identical severity
    )
    res3 = dedup.check_and_register(evt3)
    assert res3.is_duplicate is True
    assert "spatio_temporal" in res3.reason

def test_data_quality_scoring_penalties():
    now = datetime.now(timezone.utc)

    # High quality event
    high_q = NormalizedEvent(
        source_id="official-radar",
        external_id="radar-01",
        event_type="rainfall",
        title="High Precision Station Observation",
        description="Official calibrated meteorological gauge reading.",
        latitude=19.076,
        longitude=72.877,
        magnitude=24.5,
        source_url="https://example.gov/weather",
        source_reliability=0.95,
        event_timestamp=now,
    )
    w_high = DataQualityScorer.score_event(high_q, source_health_factor=1.0)
    assert w_high >= 0.70

    # Low quality / unverified event with misleading flag
    low_q = NormalizedEvent(
        source_id="social-feed",
        external_id="rumor-99",
        event_type="citizen_report",
        title="Unverified Rumor",
        latitude=0.0,
        longitude=0.0,
        source_reliability=0.30,
        event_timestamp=now - timedelta(hours=8),  # Stale
        quality_flags=["unverified", "misleading", "stale_observation"],
    )
    w_low = DataQualityScorer.score_event(low_q, source_health_factor=0.5)
    assert w_low <= 0.15
