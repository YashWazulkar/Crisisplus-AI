"""Source Health, Gateway Group Dependencies, and Reliability Tracker.

Distinguishes raw observation counts from genuinely independent monitoring sources.
Tracks shared gateway architectures, detects synchronized missingness, repeated values,
and maintains Beta conjugate distribution parameters (alpha, beta) for uncertainty-aware trust.
"""

from __future__ import annotations
import math
from datetime import datetime, timezone
from typing import Any
from ..normalization.schema import NormalizedEvent


class SourceHealthRecord:
    def __init__(
        self,
        source_id: str,
        gateway_id: str | None = None,
        source_type: str = "generic_sensor",
        initial_reliability: float = 0.85,
    ):
        self.source_id = source_id
        self.gateway_id = gateway_id
        self.source_type = source_type
        self.status = "healthy"  # healthy | degraded | stale | failed | unknown
        self.last_seen: datetime | None = None
        self.total_events = 0
        self.consecutive_stale_ticks = 0

        # Beta conjugate distribution parameters for Bayesian trust
        # Prior equivalent to ~20 observations with initial_reliability mean
        prior_sample_weight = 20.0
        self.alpha = max(1.0, prior_sample_weight * initial_reliability)
        self.beta = max(1.0, prior_sample_weight * (1.0 - initial_reliability))

        # Telemetry anomaly checks
        self.last_magnitude: float | None = None
        self.identical_value_repeats = 0
        self.impossible_value_count = 0

    @property
    def expected_reliability(self) -> float:
        return round(self.alpha / (self.alpha + self.beta), 4)

    @property
    def sample_count(self) -> int:
        return int(self.alpha + self.beta)

    @property
    def uncertainty_variance(self) -> float:
        ab = self.alpha * self.beta
        denom = ((self.alpha + self.beta) ** 2) * (self.alpha + self.beta + 1.0)
        return round(ab / denom, 5)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "gateway_id": self.gateway_id,
            "source_type": self.source_type,
            "status": self.status,
            "reliability": self.expected_reliability,
            "sample_count": self.sample_count,
            "uncertainty_variance": self.uncertainty_variance,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "total_events": self.total_events,
            "identical_value_repeats": self.identical_value_repeats,
            "impossible_value_count": self.impossible_value_count,
        }


class SourceReliabilityTracker:
    """Manages source health, gateway dependency groups, and common-cause failure detection."""

    def __init__(self):
        self.sources: dict[str, SourceHealthRecord] = {}
        self.gateway_groups: dict[str, set[str]] = {}  # gateway_id -> set of source_ids
        self.failed_gateways: set[str] = set()

    def register_event(self, event: NormalizedEvent) -> dict[str, Any]:
        """Updates source records with new event telemetry, checking for failure indicators."""
        src_id = event.source_id
        gw_id = event.gateway_id

        if src_id not in self.sources:
            self.sources[src_id] = SourceHealthRecord(
                source_id=src_id,
                gateway_id=gw_id,
                source_type=event.event_type,
                initial_reliability=event.source_reliability,
            )

        rec = self.sources[src_id]
        rec.last_seen = event.ingestion_timestamp
        rec.total_events += 1
        rec.consecutive_stale_ticks = 0

        # Update gateway mapping
        if gw_id:
            rec.gateway_id = gw_id
            self.gateway_groups.setdefault(gw_id, set()).add(src_id)

        # 1. Repeated value / frozen sensor detection
        if event.magnitude is not None:
            if rec.last_magnitude is not None and abs(event.magnitude - rec.last_magnitude) < 1e-6:
                rec.identical_value_repeats += 1
                if rec.identical_value_repeats >= 5:
                    rec.status = "degraded"
                    if "stale_observation" not in event.quality_flags:
                        event.quality_flags.append("stale_observation")
            else:
                rec.identical_value_repeats = 0
            rec.last_magnitude = event.magnitude

        # 2. Impossible value detection (e.g. negative rainfall or extreme sensor overflow)
        if event.magnitude is not None:
            if (event.event_type == "rainfall" and (event.magnitude < 0.0 or event.magnitude > 500.0)) or \
               (event.event_type == "traffic_speed" and (event.magnitude < 0.0 or event.magnitude > 250.0)):
                rec.impossible_value_count += 1
                rec.status = "failed"
                rec.beta += 2.0
                if "sensor_error" not in event.quality_flags:
                    event.quality_flags.append("sensor_error")

        # 3. Explicit gateway failure handling
        if event.event_type in ("gateway_failure", "sensor_failure"):
            rec.status = "failed"
            rec.beta += 3.0
            if gw_id:
                self.failed_gateways.add(gw_id)
                # Synchronously degrade all sensors attached to this gateway
                for s_id in self.gateway_groups.get(gw_id, set()):
                    if s_id in self.sources:
                        self.sources[s_id].status = "degraded"
        elif event.event_type == "source_recovered":
            rec.status = "healthy"
            if gw_id and gw_id in self.failed_gateways:
                self.failed_gateways.discard(gw_id)
                for s_id in self.gateway_groups.get(gw_id, set()):
                    if s_id in self.sources:
                        self.sources[s_id].status = "healthy"

        return rec.to_dict()

    def get_effective_independent_source_count(self, source_ids: list[str]) -> int:
        """
        Calculates the number of GENUINELY independent sources.
        For example: 100 sensors that share a single gateway count as 1 independent cluster!
        """
        gateways_represented: set[str] = set()
        independent_standalone: set[str] = set()

        for s_id in source_ids:
            rec = self.sources.get(s_id)
            if rec and rec.gateway_id:
                gateways_represented.add(rec.gateway_id)
            else:
                independent_standalone.add(s_id)

        # Independent sources = distinct gateways + standalone non-gateway sources
        return len(gateways_represented) + len(independent_standalone)

    def mark_stale_sources(self, current_time: datetime, timeout_seconds: float = 300.0) -> list[str]:
        """Scans for sources that have not reported within timeout window and flags them as stale."""
        stale_ids = []
        for s_id, rec in self.sources.items():
            if rec.last_seen:
                age = (current_time - rec.last_seen).total_seconds()
                if age > timeout_seconds and rec.status == "healthy":
                    rec.status = "stale"
                    rec.consecutive_stale_ticks += 1
                    stale_ids.append(s_id)
        return stale_ids

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_monitored_sources": len(self.sources),
            "healthy": sum(1 for s in self.sources.values() if s.status == "healthy"),
            "degraded": sum(1 for s in self.sources.values() if s.status == "degraded"),
            "stale": sum(1 for s in self.sources.values() if s.status == "stale"),
            "failed": sum(1 for s in self.sources.values() if s.status == "failed"),
            "active_gateway_groups": len(self.gateway_groups),
            "failed_gateways": list(self.failed_gateways),
            "sources": [s.to_dict() for s in self.sources.values()],
        }

    def reset(self):
        self.sources.clear()
        self.gateway_groups.clear()
        self.failed_gateways.clear()
