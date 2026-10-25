"""Decision Engine and Operational Response Level Recommender for CrisisPulse AI.

Computes expected-loss action recommendations across four standardized operational levels:
  WATCH    — Passive monitoring of baseline or unusual telemetry.
  PREPARE  — Pre-position evidence gathering and alert monitoring teams.
  ALERT    — Active notification of emergency coordinators; commence field verification.
  ESCALATE — Urgent strategic review for inter-agency disaster intervention.

Includes:
  - Transparent configurable expected loss matrix Loss(Action, Hypothesis).
  - Value of Information (VOI) / Optimal Stopping approximation (cost of waiting vs error cost).
  - Corroboration gates requiring >= 2 independent sources from distinct gateways for ESCALATE.
  - Alert stability and hysteresis policy to prevent flip-flops.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from ..normalization.schema import NormalizedEvent
from .stability import AlertStabilityPolicy

# Configurable Expected-loss cost matrix Loss(Action, Hypothesis)
# Normalized across both canonical and legacy hypothesis names.
DEFAULT_RESPONSE_COSTS: dict[str, dict[str, float]] = {
    "WATCH": {
        "noise": 0.0, "normal": 0.0,
        "sensor_failure": 1.2, "source_failure": 1.2,
        "isolated_incident": 7.5,
        "cascading_crisis": 18.0,
    },
    "PREPARE": {
        "noise": 2.2, "normal": 2.2,
        "sensor_failure": 2.0, "source_failure": 2.0,
        "isolated_incident": 3.8,
        "cascading_crisis": 8.0,
    },
    "ALERT": {
        "noise": 6.5, "normal": 6.5,
        "sensor_failure": 5.0, "source_failure": 5.0,
        "isolated_incident": 2.0,
        "cascading_crisis": 3.0,
    },
    "ESCALATE": {
        "noise": 13.0, "normal": 13.0,
        "sensor_failure": 10.5, "source_failure": 10.5,
        "isolated_incident": 5.2,
        "cascading_crisis": 1.0,
    },
}

RESPONSE_COSTS = DEFAULT_RESPONSE_COSTS


class DecisionEngine:
    """Calculates risk-optimal response levels with value-of-information and hysteresis stability."""

    def __init__(
        self,
        escalation_threshold: float = 0.70,
        alert_threshold: float = 0.40,
        response_costs: dict[str, dict[str, float]] | None = None,
    ):
        self.escalation_threshold = escalation_threshold
        self.alert_threshold = alert_threshold
        self.costs = response_costs or DEFAULT_RESPONSE_COSTS
        self.stability_policy = AlertStabilityPolicy(
            escalate_entry_p=escalation_threshold,
            alert_entry_p=alert_threshold,
        )

    def evaluate(
        self,
        probabilities: dict[str, float],
        recent_events: list[NormalizedEvent],
        source_health_map: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Calculates expected cost for each action, evaluates optimal stopping / VOI,
        enforces corroboration gating, and stabilizes through the hysteresis policy.
        """
        # Canonical probability lookup
        p_cascade = probabilities.get("cascading_crisis", 0.0)
        p_isolated = probabilities.get("isolated_incident", 0.0)
        p_failure = probabilities.get("sensor_failure", probabilities.get("source_failure", 0.0))
        p_noise = probabilities.get("noise", probabilities.get("normal", 0.0))

        canonical_probs = {
            "noise": p_noise,
            "sensor_failure": p_failure,
            "isolated_incident": p_isolated,
            "cascading_crisis": p_cascade,
        }

        # 1. Compute expected loss for each action: E[Loss(a)] = sum_h P(h) * Loss(a, h)
        expected_costs = {}
        for action, cost_row in self.costs.items():
            cost_val = sum(canonical_probs[h] * cost_row.get(h, 0.0) for h in canonical_probs)
            expected_costs[action] = round(cost_val, 3)

        raw_optimal_action = min(expected_costs, key=expected_costs.get)  # type: ignore

        # 2. Corroboration & Independent Source Evaluation
        critical_types = {
            "rainfall", "water_level", "road_flooding", "earthquake", "wildfire",
            "flood", "cyclone", "ambulance_delay", "hospital_demand"
        }

        independent_sources: set[str] = set()
        independent_gateways: set[str] = set()
        supporting_evidence: list[str] = []
        conflicting_evidence: list[str] = []

        latest_critical_event: NormalizedEvent | None = None

        for e in recent_events[-30:]:
            is_valid_evidence = not any(f in e.quality_flags for f in ("misleading", "correlated_report", "unverified", "retracted"))
            if e.event_type in critical_types and is_valid_evidence:
                independent_sources.add(e.source_id)
                if e.gateway_id:
                    independent_gateways.add(e.gateway_id)
                else:
                    independent_gateways.add(e.source_id)
                supporting_evidence.append(f"{e.event_type.replace('_', ' ').title()} from {e.source_id} (severity {e.severity:.2f})")
                if latest_critical_event is None or e.severity > latest_critical_event.severity:
                    latest_critical_event = e
            elif "unverified" in e.quality_flags or "misleading" in e.quality_flags:
                conflicting_evidence.append(f"Flagged unverified report from {e.source_id}: {e.title}")
            elif "retracted" in e.quality_flags:
                conflicting_evidence.append(f"Retracted report from {e.source_id}: {e.title}")

        if p_failure > 0.40:
            conflicting_evidence.append(
                f"High sensor/source failure probability ({p_failure:.1%}) indicates telemetry breakdown rather than verified physical disaster."
            )

        # Count genuinely independent clusters
        effective_independent_count = len(independent_gateways)

        # 3. Value of Information (VOI) / Optimal Stopping approximation
        # Cost of waiting 5 minutes for additional sensor corroboration vs cost of premature action
        waiting_cost_per_minute = 0.15 * p_cascade  # delay cost grows with cascade probability
        cost_of_waiting_5m = round(5.0 * waiting_cost_per_minute, 3)
        voi_savings = max(0.0, expected_costs["ESCALATE"] - expected_costs["PREPARE"]) if raw_optimal_action == "ESCALATE" else 0.0
        should_wait_for_corroboration = (effective_independent_count < 2 and p_cascade < 0.85)

        # 4. Corroboration Gating
        gated_action = raw_optimal_action
        gate_reason = ""

        if raw_optimal_action == "ESCALATE":
            if p_cascade < self.escalation_threshold:
                gated_action = "ALERT" if p_cascade >= self.alert_threshold else "PREPARE"
                gate_reason = f"Gated: Cascading probability ({p_cascade:.1%}) below escalation threshold ({self.escalation_threshold:.0%})."
            elif effective_independent_count < 2:
                gated_action = "ALERT"
                gate_reason = f"Gated: ESCALATE requires at least 2 independent verified sources (observed: {effective_independent_count})."

        # 5. Alert Stability & Hysteresis Evaluation
        stability_result = self.stability_policy.evaluate_transition(
            raw_recommended_action=gated_action,
            probabilities=canonical_probs,
            independent_sources_count=effective_independent_count,
            latest_event=latest_critical_event,
            now=now,
        )

        final_action = stability_result["stabilized_action"]
        transition_note = stability_result["block_reason"] or stability_result["override_reason"] or ""

        # Verification steps and guidance
        verification_steps = []
        if final_action == "ESCALATE":
            verification_steps = [
                "Execute mandatory verbal verification with District Emergency Operations Center (EOC).",
                "Verify automated gauge telemetry against physical CCTV intersection cameras.",
                "Confirm hospital intake coordination and pre-alert regional paramedic dispatch.",
            ]
        elif final_action == "ALERT":
            verification_steps = [
                "Dispatch traffic patrol or spotters to low-lying arterial transit choke points.",
                "Cross-reference municipal weather radar with physical stormwater sensor telemetry.",
                "Issue preliminary operational advisory to municipal response units.",
            ]
        elif final_action == "PREPARE":
            verification_steps = [
                "Inspect sensor health telemetry for intermittent gateway transmission faults.",
                "Confirm duty-officer readiness at regional monitoring desks.",
                "Review real-time catchment rainfall accumulation forecasts.",
            ]
        else:
            verification_steps = [
                "Maintain continuous background ingestion from Open-Meteo, IMD, USGS, and municipal feeds.",
                "No immediate operational intervention required.",
            ]

        rationale = (
            f"Selected {final_action} with expected loss of {expected_costs[final_action]:.2f}. "
            f"Cascading posterior is {p_cascade:.1%}, with {effective_independent_count} independent corroborated source cluster(s). "
            f"{gate_reason} {transition_note}"
        ).strip()

        return {
            "action": final_action,
            "raw_cost_optimal_action": raw_optimal_action,
            "expected_costs": expected_costs,
            "gate_reason": gate_reason,
            "transition_allowed": stability_result["transition_allowed"],
            "transition_reason": transition_note,
            "previous_action": stability_result["previous_action"],
            "time_in_state_seconds": stability_result["time_in_current_state_seconds"],
            "reasons": rationale,
            "supporting_evidence": supporting_evidence[:5],
            "conflicting_evidence": conflicting_evidence[:4],
            "confidence": round(max(0.60, 1.0 - abs(p_cascade - 0.5) * 0.4), 2),
            "effective_independent_sources": effective_independent_count,
            "cost_of_waiting_5m": cost_of_waiting_5m,
            "should_wait_for_corroboration": should_wait_for_corroboration,
            "verification_steps": verification_steps,
            "escalate_condition": f"Escalate if Cascade probability >= {self.escalation_threshold:.0%} with >= 2 independent source groups.",
            "deescalate_condition": f"De-escalate to WATCH if active hazards subside and Noise probability >= 60% for consecutive cycles.",
            "disclaimer": "CRISISPULSE DECISION SUPPORT: Autonomous emergency dispatch is strictly prohibited. Final response decisions require authorized human review.",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def reset(self):
        self.stability_policy.reset()
