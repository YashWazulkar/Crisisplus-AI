"""Base-Rate Adaptation and Seasonal Drift Tracking Engine.

Maintains background prevalence distributions across operational hypotheses,
distinguishing long-term seasonal shifts (e.g. monsoon onset in Vidarbha/Nagpur)
from sudden cascading emergencies. Bounded updates prevent catastrophic overfitting.
"""

from __future__ import annotations
import math
from datetime import datetime, timezone
from typing import Any

DEFAULT_PRIORS = {
    "noise": 0.55,
    "sensor_failure": 0.15,
    "isolated_incident": 0.20,
    "cascading_crisis": 0.10,
}

# Alias mapping for backwards compatibility
KEY_ALIASES = {
    "normal": "noise",
    "source_failure": "sensor_failure",
}


class BaseRateAdapter:
    """Tracks background event prevalence and adapts prior belief distributions safely."""

    def __init__(
        self,
        initial_priors: dict[str, float] | None = None,
        adaptation_rate: float = 0.05,
        decay_factor: float = 0.98,
        min_prior: float = 0.03,
        max_prior: float = 0.75,
    ):
        self.adaptation_rate = adaptation_rate
        self.decay_factor = decay_factor
        self.min_prior = min_prior
        self.max_prior = max_prior
        base = initial_priors or DEFAULT_PRIORS
        self.priors: dict[str, float] = self._normalize_priors(base)
        self.initial_priors = self.priors.copy()

        # Historical episode and observation counts
        self.history_records: list[dict[str, Any]] = []
        self.verified_outcomes_count: dict[str, int] = {k: 0 for k in self.priors}
        self.total_verified = 0

        # Drift tracking
        self.baseline_rainfall_rate = 12.0  # mm/h historical seasonal mean for Nagpur
        self.observed_rainfall_ema = 12.0
        self.drift_detected = False
        self.drift_metric = 0.0

    def _normalize_priors(self, raw: dict[str, float]) -> dict[str, float]:
        mapped = {}
        for k, v in raw.items():
            std_k = KEY_ALIASES.get(k, k)
            mapped[std_k] = max(self.min_prior, min(self.max_prior, float(v)))
        total = sum(mapped.values())
        return {k: round(v / total, 4) for k, v in mapped.items()}

    def record_verified_outcome(self, true_hypothesis: str, timestamp: datetime | None = None) -> dict[str, Any]:
        """
        Updates priors using verified ground truth outcomes (e.g. from official EOC debriefs).
        Never uses unverified model predictions as ground truth.
        """
        std_hyp = KEY_ALIASES.get(true_hypothesis, true_hypothesis)
        if std_hyp not in self.priors:
            return {"updated": False, "reason": f"Unknown hypothesis {true_hypothesis}"}

        now_utc = timestamp or datetime.now(timezone.utc)
        self.verified_outcomes_count[std_hyp] += 1
        self.total_verified += 1

        # Bayesian Dirichlet-like gradual update with decaying memory
        prior_before = self.priors.copy()
        target = {k: (1.0 if k == std_hyp else 0.0) for k in self.priors}

        updated = {}
        for k in self.priors:
            # Gradual step towards verified frequency with bounds
            new_val = (1.0 - self.adaptation_rate) * self.priors[k] + self.adaptation_rate * target[k]
            updated[k] = max(self.min_prior, min(self.max_prior, new_val))

        total = sum(updated.values())
        self.priors = {k: round(v / total, 4) for k, v in updated.items()}

        log_entry = {
            "timestamp": now_utc.isoformat(),
            "verified_outcome": std_hyp,
            "priors_before": prior_before,
            "priors_after": self.priors.copy(),
            "total_verified_episodes": self.total_verified,
        }
        self.history_records.append(log_entry)
        return {"updated": True, "log": log_entry}

    def update_environmental_drift(self, rainfall_mm: float) -> dict[str, Any]:
        """
        Monitors background environmental precipitation drift (e.g. onset of monsoon season in Nagpur).
        Adapts baseline noise/cascade background likelihood without blinding the system to crises.
        """
        alpha = 0.05
        self.observed_rainfall_ema = (1.0 - alpha) * self.observed_rainfall_ema + alpha * rainfall_mm
        self.drift_metric = abs(self.observed_rainfall_ema - self.baseline_rainfall_rate) / max(1.0, self.baseline_rainfall_rate)
        self.drift_detected = self.drift_metric > 0.60

        return {
            "observed_ema": round(self.observed_rainfall_ema, 2),
            "baseline_mean": round(self.baseline_rainfall_rate, 2),
            "drift_metric": round(self.drift_metric, 3),
            "drift_detected": self.drift_detected,
            "interpretation": (
                "Monsoon/seasonal baseline shift detected: Higher ambient rain is standard background condition."
                if self.drift_detected else "Nominal seasonal baseline."
            ),
        }

    def get_current_priors(self, include_aliases: bool = True) -> dict[str, float]:
        res = self.priors.copy()
        if include_aliases:
            # Add backwards-compatible keys
            res["normal"] = res.get("noise", 0.55)
            res["source_failure"] = res.get("sensor_failure", 0.15)
        return res

    def reset(self):
        self.priors = self.initial_priors.copy()
        self.history_records.clear()
        self.verified_outcomes_count = {k: 0 for k in self.priors}
        self.total_verified = 0
        self.observed_rainfall_ema = self.baseline_rainfall_rate
        self.drift_detected = False
        self.drift_metric = 0.0
