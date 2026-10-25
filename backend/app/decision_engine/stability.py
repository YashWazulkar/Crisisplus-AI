"""Alert Stability, Hysteresis Policy, and State Transition Engine.

Prevents volatile response oscillations (e.g. ESCALATE -> WATCH -> ESCALATE)
using dual-threshold hysteresis bands, consecutive persistence counters,
time-based de-escalation cooldowns, and instant emergency overrides for rapid deterioration.
Maintains a full audit record of every transition decision and blocking rationale.
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any
from ..normalization.schema import NormalizedEvent

ACTION_LEVELS = ["WATCH", "PREPARE", "ALERT", "ESCALATE"]
ACTION_ORDER = {"WATCH": 0, "PREPARE": 1, "ALERT": 2, "ESCALATE": 3}


class AlertStabilityPolicy:
    """Enforces hysteresis and cooldowns to guarantee operational stability."""

    def __init__(
        self,
        escalate_entry_p: float = 0.70,
        escalate_exit_p: float = 0.50,
        alert_entry_p: float = 0.40,
        alert_exit_p: float = 0.28,
        min_persistence_cycles: int = 2,
        deescalate_cooldown_seconds: float = 180.0,
    ):
        self.escalate_entry_p = escalate_entry_p
        self.escalate_exit_p = escalate_exit_p
        self.alert_entry_p = alert_entry_p
        self.alert_exit_p = alert_exit_p
        self.min_persistence_cycles = min_persistence_cycles
        self.deescalate_cooldown_seconds = deescalate_cooldown_seconds

        # State tracking
        self.current_action = "WATCH"
        self.last_transition_time = datetime.now(timezone.utc)
        self.consecutive_recommended_action = "WATCH"
        self.consecutive_count = 0
        self.transition_history: list[dict[str, Any]] = []

    def evaluate_transition(
        self,
        raw_recommended_action: str,
        probabilities: dict[str, float],
        independent_sources_count: int,
        latest_event: NormalizedEvent | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Determines whether to accept, dampen, or block an action change.
        Returns stabilized action, allowed flag, and comprehensive explanation.
        """
        current_time = now or datetime.now(timezone.utc)
        time_in_current_state = (current_time - self.last_transition_time).total_seconds()

        p_cascade = probabilities.get("cascading_crisis", 0.0)
        p_isolated = probabilities.get("isolated_incident", 0.0)
        p_failure = probabilities.get("sensor_failure", probabilities.get("source_failure", 0.0))

        # 1. Update consecutive counter
        if raw_recommended_action == self.consecutive_recommended_action:
            self.consecutive_count += 1
        else:
            self.consecutive_recommended_action = raw_recommended_action
            self.consecutive_count = 1

        target_action = raw_recommended_action
        target_rank = ACTION_ORDER[target_action]
        current_rank = ACTION_ORDER[self.current_action]

        # 2. EMERGENCY OVERRIDE CHECK
        # If an extreme event occurs (cloudburst > 70 mm/h, severe quake, rapid surge), escalate immediately!
        is_emergency_override = False
        override_reason = ""
        if latest_event and latest_event.severity >= 0.85:
            if latest_event.event_type in ("rainfall", "road_flooding", "earthquake", "flood", "cyclone"):
                is_emergency_override = True
                override_reason = f"EMERGENCY OVERRIDE: Critical {latest_event.event_type} severity {latest_event.severity:.2f} triggered zero-latency escalation bypass."
                if target_rank > current_rank:
                    target_action = raw_recommended_action

        # 3. ESCALATION vs DE-ESCALATION LOGIC
        transition_allowed = True
        block_reason = ""

        if is_emergency_override:
            final_action = target_action
        elif target_rank > current_rank:
            # ESCALATING (Moving to a higher readiness posture)
            # Escalations are permitted quickly if corroboration and entry thresholds are met
            if target_action == "ESCALATE":
                if p_cascade < self.escalate_entry_p:
                    transition_allowed = False
                    block_reason = f"Blocked ESCALATE: Cascade probability ({p_cascade:.1%}) below entry threshold ({self.escalate_entry_p:.0%})."
                    final_action = "ALERT" if p_cascade >= self.alert_entry_p else self.current_action
                elif independent_sources_count < 2:
                    transition_allowed = False
                    block_reason = f"Blocked ESCALATE: Requires >= 2 independent sources (observed: {independent_sources_count})."
                    final_action = "ALERT"
                else:
                    final_action = "ESCALATE"
            elif target_action == "ALERT":
                if p_cascade < self.alert_entry_p and p_isolated < 0.50:
                    transition_allowed = False
                    block_reason = f"Blocked ALERT: Evidence probability does not meet alert criteria."
                    final_action = self.current_action
                else:
                    final_action = "ALERT"
            else:
                final_action = target_action

        elif target_rank < current_rank:
            # DE-ESCALATING (Lowering response posture)
            # Enforce Hysteresis, Cooldowns, and Persistence!
            if time_in_current_state < self.deescalate_cooldown_seconds:
                transition_allowed = False
                block_reason = (
                    f"Blocked de-escalation from {self.current_action} to {target_action}: "
                    f"State cooldown active ({int(self.deescalate_cooldown_seconds - time_in_current_state)}s remaining)."
                )
                final_action = self.current_action

            elif self.consecutive_count < self.min_persistence_cycles:
                transition_allowed = False
                block_reason = (
                    f"Blocked de-escalation: Requires {self.min_persistence_cycles} consecutive calm assessments "
                    f"(observed: {self.consecutive_count})."
                )
                final_action = self.current_action

            elif self.current_action == "ESCALATE" and p_cascade >= self.escalate_exit_p:
                # Hysteresis band check: must drop below exit threshold (50%), not just entry threshold (70%)
                transition_allowed = False
                block_reason = (
                    f"Hysteresis active: Cannot leave ESCALATE until cascade probability drops below "
                    f"exit threshold ({self.escalate_exit_p:.0%}) (current: {p_cascade:.1%})."
                )
                final_action = "ESCALATE"

            elif self.current_action == "ALERT" and p_cascade >= self.alert_exit_p:
                transition_allowed = False
                block_reason = (
                    f"Hysteresis active: Cannot leave ALERT until cascade probability drops below "
                    f"exit threshold ({self.alert_exit_p:.0%}) (current: {p_cascade:.1%})."
                )
                final_action = "ALERT"

            else:
                final_action = target_action

        else:
            final_action = self.current_action

        # 4. Record transition if action actually changes
        if final_action != self.current_action:
            record = {
                "timestamp": current_time.isoformat(),
                "previous_action": self.current_action,
                "new_action": final_action,
                "transition_type": "escalation" if ACTION_ORDER[final_action] > ACTION_ORDER[self.current_action] else "de-escalation",
                "time_in_previous_state_seconds": round(time_in_current_state, 1),
                "reason": override_reason or ("Threshold and persistence verified" if transition_allowed else block_reason),
            }
            self.transition_history.append(record)
            self.current_action = final_action
            self.last_transition_time = current_time

        return {
            "stabilized_action": final_action,
            "raw_recommended_action": raw_recommended_action,
            "previous_action": self.current_action,
            "transition_allowed": transition_allowed,
            "block_reason": block_reason,
            "override_active": is_emergency_override,
            "override_reason": override_reason,
            "time_in_current_state_seconds": round(time_in_current_state, 1),
            "consecutive_calm_cycles": self.consecutive_count,
        }

    def reset(self):
        self.current_action = "WATCH"
        self.last_transition_time = datetime.now(timezone.utc)
        self.consecutive_recommended_action = "WATCH"
        self.consecutive_count = 0
        self.transition_history.clear()
