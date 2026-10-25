"""Data Quality and Trust Scoring Module.

Computes multi-attribute quality scores for incoming events, measuring schema completeness,
temporal decay, source reliability, and correlation penalties.
"""

from __future__ import annotations
import math
from datetime import datetime, timezone
from ..normalization.schema import NormalizedEvent

class DataQualityScorer:
    """Calculates evidence weighting and data quality score."""

    # Half-life for evidence freshness decay in hours
    FRESHNESS_HALF_LIFE_HOURS = 2.0

    @classmethod
    def score_event(cls, event: NormalizedEvent, source_health_factor: float = 1.0) -> float:
        """Computes a quality weight in [0.05, 1.0] used to temper Bayesian likelihood updates."""

        # 1. Base source trust
        base_trust = max(0.1, min(1.0, event.source_reliability * source_health_factor))

        # 2. Completeness score (0.0 to 1.0)
        completeness = 0.5
        if event.latitude != 0.0 or event.longitude != 0.0:
            completeness += 0.15
        if event.magnitude is not None:
            completeness += 0.15
        if event.source_url:
            completeness += 0.10
        if event.title and len(event.title) > 5:
            completeness += 0.10

        # 3. Freshness decay
        now_utc = datetime.now(timezone.utc)
        age_hours = max(0.0, (now_utc - event.event_timestamp).total_seconds() / 3600.0)
        freshness = math.exp(-math.log(2) * (age_hours / cls.FRESHNESS_HALF_LIFE_HOURS))

        # 4. Diagnostic flag penalties
        penalty = 1.0
        flags = set(event.quality_flags)

        if "unverified" in flags or event.verification_status == "unverified":
            penalty *= 0.5
        if "correlated_report" in flags or "correlated" in flags:
            penalty *= 0.65
        if "misleading" in flags or event.payload.get("misleading"):
            penalty *= 0.20
        if "stale_observation" in flags:
            penalty *= 0.40
        if "null_island_coordinates" in flags:
            penalty *= 0.30

        # Gateway correlation discount: if multiple events share one gateway, they aren't independent
        if event.gateway_id:
            penalty *= 0.85

        composite_weight = base_trust * (0.6 * freshness + 0.4 * completeness) * penalty
        return max(0.05, min(1.0, round(composite_weight, 4)))
