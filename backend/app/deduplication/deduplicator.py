"""Deduplication and Event Correlation Engine.

Prevents duplicate event insertion and downweights spatial-temporal duplicates
to ensure independent evidence assumptions are not violated.
"""

from __future__ import annotations
import math
from datetime import datetime, timezone
from typing import Any
from ..normalization.schema import NormalizedEvent

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in kilometers."""
    R = 6371.0  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class DeduplicationResult:
    def __init__(self, is_duplicate: bool, reason: str | None = None, correlated_event_id: str | None = None):
        self.is_duplicate = is_duplicate
        self.reason = reason
        self.correlated_event_id = correlated_event_id

    def __bool__(self) -> bool:
        return self.is_duplicate

class EventDeduplicator:
    """Tracks seen external IDs and detects spatial-temporal proximity duplicates."""

    def __init__(self, max_cache_size: int = 5000, spatial_window_km: float = 15.0, time_window_seconds: float = 900.0):
        self.max_cache_size = max_cache_size
        self.spatial_window_km = spatial_window_km
        self.time_window_seconds = time_window_seconds
        self.seen_exact_ids: set[str] = set()
        self.seen_source_external_ids: set[tuple[str, str]] = set()
        self.recent_events_buffer: list[dict[str, Any]] = []

    def reset(self):
        self.seen_exact_ids.clear()
        self.seen_source_external_ids.clear()
        self.recent_events_buffer.clear()

    def check_and_register(self, event: NormalizedEvent) -> DeduplicationResult:
        """Check if event is an exact duplicate or spatio-temporally correlated."""

        # 1. Exact Event ID check
        if event.event_id in self.seen_exact_ids:
            return DeduplicationResult(True, reason="duplicate_internal_event_id")

        # 2. Source + External ID check
        source_ext_key = (event.source_id, event.external_id)
        if source_ext_key in self.seen_source_external_ids:
            return DeduplicationResult(True, reason=f"duplicate_source_external_id: {event.source_id}:{event.external_id}")

        # 3. Spatio-temporal cluster check for similar hazard
        for prev in reversed(self.recent_events_buffer[-100:]):
            if prev["event_type"] == event.event_type:
                time_diff = abs((event.event_timestamp - prev["event_timestamp"]).total_seconds())
                if time_diff <= self.time_window_seconds:
                    dist_km = haversine_distance_km(event.latitude, event.longitude, prev["latitude"], prev["longitude"])
                    if dist_km <= self.spatial_window_km:
                        # Correlated event (e.g. aftershock, same fire cluster, or identical weather station report)
                        if "correlated_report" not in event.quality_flags:
                            event.quality_flags.append("correlated_report")
                        # If external ID is different but location/time is identical, it's a correlated observation
                        # We allow it through if severity differs significantly, otherwise classify as near-duplicate
                        if abs(event.severity - prev["severity"]) < 0.05 and event.source_id == prev["source_id"]:
                            return DeduplicationResult(
                                True,
                                reason=f"spatio_temporal_duplicate within {dist_km:.1f}km and {time_diff/60:.1f}min",
                                correlated_event_id=prev["event_id"]
                            )

        # Register event
        self.seen_exact_ids.add(event.event_id)
        self.seen_source_external_ids.add(source_ext_key)
        self.recent_events_buffer.append({
            "event_id": event.event_id,
            "source_id": event.source_id,
            "event_type": event.event_type,
            "latitude": event.latitude,
            "longitude": event.longitude,
            "event_timestamp": event.event_timestamp,
            "severity": event.severity,
        })

        # Cache management
        if len(self.recent_events_buffer) > self.max_cache_size:
            self.recent_events_buffer = self.recent_events_buffer[-int(self.max_cache_size * 0.75):]
        if len(self.seen_exact_ids) > self.max_cache_size * 2:
            self.seen_exact_ids.clear()
            self.seen_source_external_ids.clear()

        return DeduplicationResult(False)
