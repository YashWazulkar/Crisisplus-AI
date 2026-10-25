"""Base Ingestion Adapter Interface for CrisisPulse AI."""

from __future__ import annotations
import abc
from datetime import datetime, timezone
from typing import Any
from ..normalization.schema import NormalizedEvent

class BaseAdapter(abc.ABC):
    """Abstract base class for all real-time and scheduled external data adapters."""

    def __init__(self, name: str, source_type: str, polling_interval_seconds: int = 60):
        self.name = name
        self.source_type = source_type
        self.polling_interval_seconds = polling_interval_seconds
        self.enabled = True
        self.status: str = "healthy"  # healthy | degraded | error | not_configured | awaiting_api_key
        self.last_fetch_time: datetime | None = None
        self.last_success_time: datetime | None = None
        self.last_error: str | None = None
        self.latency_ms: float = 0.0
        self.records_accepted: int = 0
        self.records_rejected: int = 0
        self.consecutive_failures: int = 0
        self.backoff_seconds: float = 0.0

    @abc.abstractmethod
    async def fetch_events(self) -> list[NormalizedEvent]:
        """Fetch records from upstream API, parse, and return NormalizedEvent instances."""
        pass

    def record_success(self, count: int, latency_ms: float):
        self.status = "healthy"
        self.last_fetch_time = datetime.now(timezone.utc)
        self.last_success_time = self.last_fetch_time
        self.latency_ms = round(latency_ms, 1)
        self.records_accepted += count
        self.consecutive_failures = 0
        self.backoff_seconds = 0.0
        self.last_error = None

    def record_failure(self, error: Exception | str, status: str = "error"):
        self.status = status
        self.last_fetch_time = datetime.now(timezone.utc)
        self.last_error = str(error)
        self.consecutive_failures += 1
        # Exponential backoff up to 5 minutes
        self.backoff_seconds = min(300.0, 5.0 * (2 ** min(self.consecutive_failures, 6)))

    def health_status(self) -> dict[str, Any]:
        """Returns structured health telemetry for operational monitoring."""
        now_utc = datetime.now(timezone.utc)
        freshness_sec = None
        if self.last_success_time:
            freshness_sec = round((now_utc - self.last_success_time).total_seconds(), 1)

        return {
            "source_id": self.name,
            "source_type": self.source_type,
            "status": self.status,
            "enabled": self.enabled,
            "polling_interval_seconds": self.polling_interval_seconds,
            "last_fetch": self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
            "data_freshness_seconds": freshness_sec,
            "latency_ms": self.latency_ms,
            "records_accepted": self.records_accepted,
            "records_rejected": self.records_rejected,
            "error_message": self.last_error,
            "consecutive_failures": self.consecutive_failures,
        }
