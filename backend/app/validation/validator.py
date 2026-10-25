"""Event Validation Module.

Performs strict bounds checking, coordinate validation, timestamp sanity checks,
and diagnostic flag assignment for incoming data records.
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Tuple
from ..normalization.schema import NormalizedEvent

class ValidationResult:
    def __init__(self, is_valid: bool, rejection_reason: str | None = None, quality_flags: list[str] | None = None):
        self.is_valid = is_valid
        self.rejection_reason = rejection_reason
        self.quality_flags = quality_flags or []

    def __bool__(self) -> bool:
        return self.is_valid

class EventValidator:
    """Validates raw and normalized events before admitting them to the engine or persistence."""

    MAX_FUTURE_SKEW_MINUTES = 15
    MAX_HISTORICAL_AGE_DAYS = 365

    @classmethod
    def validate(cls, event: NormalizedEvent) -> ValidationResult:
        flags: list[str] = list(event.quality_flags)

        # 1. Geographic Bounds Check
        if not (-90.0 <= event.latitude <= 90.0):
            return ValidationResult(False, f"Latitude {event.latitude} out of valid range [-90, 90]")
        if not (-180.0 <= event.longitude <= 180.0):
            return ValidationResult(False, f"Longitude {event.longitude} out of valid range [-180, 180]")

        # Null island check
        if abs(event.latitude) < 0.001 and abs(event.longitude) < 0.001:
            flags.append("null_island_coordinates")

        # 2. Timestamp sanity
        now_utc = datetime.now(timezone.utc)
        if event.event_timestamp > now_utc + timedelta(minutes=cls.MAX_FUTURE_SKEW_MINUTES):
            return ValidationResult(
                False,
                f"Event timestamp {event.event_timestamp.isoformat()} is in the future beyond acceptable clock skew"
            )

        if event.event_timestamp < now_utc - timedelta(days=cls.MAX_HISTORICAL_AGE_DAYS):
            flags.append("historical_record_exceeds_age_threshold")

        # Age calculation at ingestion
        age_seconds = max(0.0, (event.ingestion_timestamp - event.event_timestamp).total_seconds())
        if age_seconds > 3600 * 6:
            flags.append("delayed_ingestion_over_6h")
        elif age_seconds > 3600 * 24:
            flags.append("stale_observation")

        # 3. Severity & Measurement bounds
        if not (0.0 <= event.severity <= 1.0):
            return ValidationResult(False, f"Severity {event.severity} outside [0.0, 1.0]")

        if event.magnitude is not None and event.magnitude < 0.0 and event.event_type != "temperature_anomaly":
            return ValidationResult(False, f"Magnitude {event.magnitude} cannot be negative for {event.event_type}")

        # 4. Source reliability and confidence bounds
        if not (0.0 <= event.source_reliability <= 1.0):
            return ValidationResult(False, f"Reliability {event.source_reliability} outside [0.0, 1.0]")
        if not (0.0 <= event.confidence <= 1.0):
            return ValidationResult(False, f"Confidence {event.confidence} outside [0.0, 1.0]")

        # 5. Identifier completeness
        if not event.external_id or not str(event.external_id).strip():
            return ValidationResult(False, "Missing required external_id")

        if not event.source_id or not str(event.source_id).strip():
            return ValidationResult(False, "Missing required source_id")

        # Attach any discovered flags
        event.quality_flags = sorted(list(set(flags)))
        event.data_freshness_seconds = age_seconds

        return ValidationResult(True, quality_flags=event.quality_flags)
