"""Event Retraction, Correction, and Out-of-Order Message Processing Engine.

Ensures that retracted reports stop contributing positive evidence to crisis posteriors,
corrected reports supersede previous measurements without double counting,
and delayed/out-of-order events are placed in chronological sequence.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from ..normalization.schema import NormalizedEvent


class EventRetractionManager:
    """Maintains active event lifecycle, retractions, corrections, and chronological replay."""

    def __init__(self, max_history: int = 500):
        self.max_history = max_history
        self.active_events: dict[str, NormalizedEvent] = {}  # event_id -> NormalizedEvent
        self.retracted_event_ids: set[str] = set()
        self.superseded_event_ids: dict[str, str] = {}  # old_id -> new_id
        self.retraction_audit_log: list[dict[str, Any]] = []

    def process_incoming_event(self, event: NormalizedEvent) -> dict[str, Any]:
        """
        Evaluates incoming event for retractions, corrections, or delayed arrival.
        Returns:
          {
            "is_retraction": bool,
            "is_correction": bool,
            "is_out_of_order": bool,
            "target_event_id": str | None,
            "action": "inserted" | "retracted" | "superseded" | "duplicate_retraction",
            "log": dict | None,
          }
        """
        now_utc = datetime.now(timezone.utc)
        payload = event.payload or {}

        # 1. Check if this is an explicit retraction
        retracted_id = payload.get("retracted_event_id") or (
            event.external_id if event.event_type == "retraction" else None
        )

        if event.event_type == "retraction" or "retraction" in event.quality_flags or retracted_id:
            target_id = retracted_id or event.external_id
            if target_id in self.retracted_event_ids:
                return {
                    "is_retraction": True,
                    "is_correction": False,
                    "is_out_of_order": False,
                    "target_event_id": target_id,
                    "action": "duplicate_retraction",
                    "log": None,
                }

            self.retracted_event_ids.add(target_id)
            if target_id in self.active_events:
                orig = self.active_events[target_id]
                orig.quality_flags.append("retracted")
                orig.verification_status = "retracted"

            log_entry = {
                "timestamp": now_utc.isoformat(),
                "type": "retraction",
                "retraction_event_id": event.event_id,
                "retracted_target_id": target_id,
                "source_id": event.source_id,
                "reason": payload.get("reason", "Source issued official retraction / false report notice"),
            }
            self.retraction_audit_log.append(log_entry)
            return {
                "is_retraction": True,
                "is_correction": False,
                "is_out_of_order": False,
                "target_event_id": target_id,
                "action": "retracted",
                "log": log_entry,
            }

        # 2. Check if this is a correction superseding an earlier event
        supersedes_id = payload.get("supersedes_event_id") or payload.get("replaces_id")
        if supersedes_id:
            self.superseded_event_ids[supersedes_id] = event.event_id
            if supersedes_id in self.active_events:
                orig = self.active_events[supersedes_id]
                orig.quality_flags.append("superseded")

            log_entry = {
                "timestamp": now_utc.isoformat(),
                "type": "correction",
                "new_event_id": event.event_id,
                "superseded_id": supersedes_id,
                "source_id": event.source_id,
                "magnitude_before": orig.magnitude if supersedes_id in self.active_events else None,
                "magnitude_after": event.magnitude,
                "reason": payload.get("reason", "Sensor recalibration / revised observation"),
            }
            self.retraction_audit_log.append(log_entry)
            self.active_events[event.event_id] = event
            return {
                "is_retraction": False,
                "is_correction": True,
                "is_out_of_order": False,
                "target_event_id": supersedes_id,
                "action": "superseded",
                "log": log_entry,
            }

        # 3. Check for out-of-order arrival (event_timestamp significantly earlier than recent observations)
        is_out_of_order = False
        if self.active_events:
            max_recent_ts = max(e.event_timestamp for e in list(self.active_events.values())[-10:])
            if (max_recent_ts - event.event_timestamp).total_seconds() > 120.0:
                is_out_of_order = True
                event.quality_flags.append("delayed_arrival")

        self.active_events[event.event_id] = event

        # Bounded cache eviction
        if len(self.active_events) > self.max_history:
            oldest_keys = list(self.active_events.keys())[:int(self.max_history * 0.25)]
            for k in oldest_keys:
                del self.active_events[k]

        return {
            "is_retraction": False,
            "is_correction": False,
            "is_out_of_order": is_out_of_order,
            "target_event_id": None,
            "action": "inserted",
            "log": None,
        }

    def get_valid_chronological_events(self, limit: int = 50) -> list[NormalizedEvent]:
        """Returns non-retracted events sorted by physical event_timestamp (earliest to latest)."""
        valid = [
            e for e in self.active_events.values()
            if e.event_id not in self.retracted_event_ids and "retracted" not in e.quality_flags
        ]
        valid.sort(key=lambda x: x.event_timestamp)
        return valid[-limit:]

    def reset(self):
        self.active_events.clear()
        self.retracted_event_ids.clear()
        self.superseded_event_ids.clear()
        self.retraction_audit_log.clear()
