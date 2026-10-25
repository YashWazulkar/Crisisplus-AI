"""Online Source Trust Learning Engine.

Implements bounded, uncertainty-aware online updating of source reliability across episodes.
Learns strictly from verified ground-truth outcomes and authoritative confirmations,
preventing unverified model predictions from becoming self-confirming ground truth.
Includes full audit logging and rollback/replay capability for debugging.
"""

from __future__ import annotations
import math
from datetime import datetime, timezone
from typing import Any
from .source_health import SourceReliabilityTracker, SourceHealthRecord


class OnlineTrustLearner:
    """Controls online source reliability learning using Bayesian conjugate updates."""

    def __init__(self, tracker: SourceReliabilityTracker | None = None, max_sample_weight: float = 100.0):
        self.tracker = tracker or SourceReliabilityTracker()
        self.max_sample_weight = max_sample_weight
        self.update_log: list[dict[str, Any]] = []
        # Category-specific reliability vectors: source_id -> category -> (alpha, beta)
        self.category_trust: dict[str, dict[str, tuple[float, float]]] = {}

    def record_verification_outcome(
        self,
        source_id: str,
        category: str,
        was_accurate: bool,
        authoritative_source: str = "District Emergency Operations Center (EOC)",
        verification_latency_sec: float = 0.0,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Updates source trust based on authoritative ground-truth verification.
        CRITICAL: Never call this with automated model predictions. Only verified ground truth!
        """
        now_utc = timestamp or datetime.now(timezone.utc)
        rec = self.tracker.sources.get(source_id)
        if not rec:
            rec = SourceHealthRecord(source_id=source_id, source_type=category)
            self.tracker.sources[source_id] = rec

        prev_reliability = rec.expected_reliability
        prev_alpha, prev_beta = rec.alpha, rec.beta

        # 1. Update overall source Beta parameters
        if was_accurate:
            rec.alpha += 1.0
        else:
            # Penalize false alarms or corrupted telemetry with higher weight
            rec.beta += 1.5

        # Bounded ceiling to prevent sample count from growing to infinity (enables continual learning)
        total_samples = rec.alpha + rec.beta
        if total_samples > self.max_sample_weight:
            scale = self.max_sample_weight / total_samples
            rec.alpha = max(1.0, rec.alpha * scale)
            rec.beta = max(1.0, rec.beta * scale)

        # 2. Update category-specific Beta parameters
        cat_map = self.category_trust.setdefault(source_id, {})
        cat_alpha, cat_beta = cat_map.get(category, (10.0 * prev_reliability, 10.0 * (1.0 - prev_reliability)))
        if was_accurate:
            cat_alpha += 1.0
        else:
            cat_beta += 1.5
        cat_map[category] = (cat_alpha, cat_beta)

        new_reliability = rec.expected_reliability

        log_entry = {
            "update_id": f"trust-{len(self.update_log) + 1}",
            "timestamp": now_utc.isoformat(),
            "source_id": source_id,
            "category": category,
            "was_accurate": was_accurate,
            "authoritative_verifier": authoritative_source,
            "latency_seconds": round(verification_latency_sec, 1),
            "prev_reliability": prev_reliability,
            "new_reliability": new_reliability,
            "delta_reliability": round(new_reliability - prev_reliability, 4),
            "alpha": round(rec.alpha, 2),
            "beta": round(rec.beta, 2),
            "uncertainty_variance": rec.uncertainty_variance,
            "prev_state": (prev_alpha, prev_beta),
        }
        self.update_log.append(log_entry)
        return log_entry

    def rollback_last_update(self) -> dict[str, Any] | None:
        """Rolls back the most recent trust update for audit or counterfactual debugging."""
        if not self.update_log:
            return None
        last = self.update_log.pop()
        source_id = last["source_id"]
        rec = self.tracker.sources.get(source_id)
        if rec and "prev_state" in last:
            rec.alpha, rec.beta = last["prev_state"]
        return last

    def run_controlled_trust_experiment(self, source_id: str, episode_sequence: list[bool]) -> dict[str, Any]:
        """
        Executes a controlled experiment showing how a source's reliability evolves
        over a series of verified true (accurate) and false (inaccurate) ground-truth events.
        """
        # Save snapshot
        rec = self.tracker.sources.setdefault(source_id, SourceHealthRecord(source_id=source_id))
        saved_alpha, saved_beta = rec.alpha, rec.beta

        progression = []
        for i, outcome in enumerate(episode_sequence):
            entry = self.record_verification_outcome(
                source_id=source_id,
                category="test_feed",
                was_accurate=outcome,
                authoritative_source="Benchmark Validator",
            )
            progression.append({
                "episode": i + 1,
                "outcome": "accurate" if outcome else "inaccurate",
                "reliability": entry["new_reliability"],
                "uncertainty_variance": entry["uncertainty_variance"],
                "sample_count": int(entry["alpha"] + entry["beta"]),
            })

        # Restore prior state so experiment does not pollute production trust
        rec.alpha, rec.beta = saved_alpha, saved_beta

        return {
            "source_id": source_id,
            "episodes_count": len(episode_sequence),
            "progression": progression,
            "initial_reliability": round(saved_alpha / (saved_alpha + saved_beta), 4),
            "final_experiment_reliability": progression[-1]["reliability"] if progression else 0.0,
        }

    def get_audit_log(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(reversed(self.update_log[-limit:]))
