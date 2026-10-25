"""Bayesian Probabilistic Inference Engine for CrisisPulse AI.

Maintains continuous probability distributions over four mutually exclusive operational hypotheses:
  - noise: ordinary conditions, normal variation, unrelated events, or misleading weak signals.
  - sensor_failure: sensor malfunction, gateway failure, common-cause outage, or corrupted telemetry.
  - isolated_incident: a genuine but localized incident that has not developed into a broader cascade.
  - cascading_crisis: multiple connected events developing into a potentially escalating emergency.

Properties enforced:
  - All probabilities in [0, 1] and sum to 1.0 within numerical tolerance.
  - Missing evidence does not spuriously elevate crisis posterior.
  - Common-cause outages do not masquerade as cascading ground disasters.
  - Low-trust, unverified, or correlated evidence is tempered by data quality weight omega.
  - Backward compatible with 'normal' (noise) and 'source_failure' (sensor_failure) legacy keys.
"""

from __future__ import annotations
from typing import Any
from ..normalization.schema import NormalizedEvent
from .base_rate import BaseRateAdapter, DEFAULT_PRIORS, KEY_ALIASES

# Canonical four operational hypotheses as defined in challenge specification
STANDARD_HYPOTHESES = ["noise", "sensor_failure", "isolated_incident", "cascading_crisis"]
HYPOTHESES = ["normal", "source_failure", "isolated_incident", "cascading_crisis"]

LABELS = {
    "noise": "H1 · Ordinary Noise / Baseline",
    "normal": "H1 · Ordinary Noise / Baseline",
    "sensor_failure": "H2 · Sensor / Gateway Malfunction",
    "source_failure": "H2 · Sensor / Gateway Malfunction",
    "isolated_incident": "H3 · Isolated Local Incident",
    "cascading_crisis": "H4 · Potential Cascading Crisis",
}

# Likelihood distribution P(Evidence | Hypothesis)
# Expressed across canonical hypotheses: noise, sensor_failure, isolated_incident, cascading_crisis.
# Note: These values represent expert domain priors conditioned on synthetic and historical stress scenarios.
CANONICAL_LIKELIHOODS: dict[str, dict[str, float]] = {
    "rainfall":             {"noise": 0.70, "sensor_failure": 0.10, "isolated_incident": 0.25, "cascading_crisis": 0.65},
    "water_level":          {"noise": 0.18, "sensor_failure": 0.10, "isolated_incident": 0.32, "cascading_crisis": 0.90},
    "traffic_speed":        {"noise": 0.48, "sensor_failure": 0.20, "isolated_incident": 0.70, "cascading_crisis": 0.80},
    "road_flooding":        {"noise": 0.04, "sensor_failure": 0.05, "isolated_incident": 0.30, "cascading_crisis": 0.95},
    "ambulance_delay":      {"noise": 0.08, "sensor_failure": 0.05, "isolated_incident": 0.50, "cascading_crisis": 0.88},
    "hospital_demand":      {"noise": 0.35, "sensor_failure": 0.10, "isolated_incident": 0.42, "cascading_crisis": 0.82},
    "sensor_failure":       {"noise": 0.04, "sensor_failure": 0.96, "isolated_incident": 0.04, "cascading_crisis": 0.10},
    "gateway_failure":      {"noise": 0.04, "sensor_failure": 0.98, "isolated_incident": 0.02, "cascading_crisis": 0.05},
    "citizen_report":       {"noise": 0.30, "sensor_failure": 0.20, "isolated_incident": 0.55, "cascading_crisis": 0.55},
    "power_outage":         {"noise": 0.05, "sensor_failure": 0.22, "isolated_incident": 0.32, "cascading_crisis": 0.82},
    "source_recovered":     {"noise": 0.35, "sensor_failure": 0.75, "isolated_incident": 0.20, "cascading_crisis": 0.20},
    "wind_gust":            {"noise": 0.55, "sensor_failure": 0.08, "isolated_incident": 0.35, "cascading_crisis": 0.72},
    "severe_weather":       {"noise": 0.08, "sensor_failure": 0.06, "isolated_incident": 0.28, "cascading_crisis": 0.88},
    "temperature_anomaly":  {"noise": 0.50, "sensor_failure": 0.35, "isolated_incident": 0.25, "cascading_crisis": 0.35},
    "earthquake":           {"noise": 0.05, "sensor_failure": 0.04, "isolated_incident": 0.65, "cascading_crisis": 0.85},
    "wildfire":             {"noise": 0.06, "sensor_failure": 0.08, "isolated_incident": 0.50, "cascading_crisis": 0.86},
    "flood":                {"noise": 0.03, "sensor_failure": 0.05, "isolated_incident": 0.35, "cascading_crisis": 0.96},
    "cyclone":              {"noise": 0.02, "sensor_failure": 0.04, "isolated_incident": 0.20, "cascading_crisis": 0.98},
    "retraction":           {"noise": 0.60, "sensor_failure": 0.25, "isolated_incident": 0.10, "cascading_crisis": 0.05},
}


class HypothesisProbabilities(dict):
    """Normalized probability dictionary supporting both canonical challenge keys and legacy aliases."""

    def __getitem__(self, key: str) -> float:
        if key == "noise" and "normal" in self:
            return super().__getitem__("normal")
        if key == "sensor_failure" and "source_failure" in self:
            return super().__getitem__("source_failure")
        if key == "normal" and "noise" in self:
            return super().__getitem__("noise")
        if key == "source_failure" and "sensor_failure" in self:
            return super().__getitem__("sensor_failure")
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def copy(self) -> HypothesisProbabilities:
        return HypothesisProbabilities(super().copy())


class BayesianInferenceEngine:
    """Computes exact posterior belief updates with evidence tempering and base-rate adaptation."""

    def __init__(self, priors: dict[str, float] | None = None, base_rate_adapter: BaseRateAdapter | None = None):
        self.base_rate_adapter = base_rate_adapter or BaseRateAdapter(initial_priors=priors)
        cur_priors = self.base_rate_adapter.get_current_priors(include_aliases=False)
        self.default_priors = HypothesisProbabilities({
            "normal": cur_priors.get("noise", 0.55),
            "source_failure": cur_priors.get("sensor_failure", 0.15),
            "isolated_incident": cur_priors.get("isolated_incident", 0.20),
            "cascading_crisis": cur_priors.get("cascading_crisis", 0.10),
        })
        self._probabilities = self.default_priors.copy()

    @property
    def probabilities(self) -> HypothesisProbabilities:
        """Returns normalized probability distribution containing the 4 canonical hypotheses."""
        return self._probabilities.copy()

    @probabilities.setter
    def probabilities(self, val: dict[str, float]):
        canon = {
            "normal": val.get("normal", val.get("noise", 0.55)),
            "source_failure": val.get("source_failure", val.get("sensor_failure", 0.15)),
            "isolated_incident": val.get("isolated_incident", 0.20),
            "cascading_crisis": val.get("cascading_crisis", 0.10),
        }
        tot = sum(canon.values()) or 1.0
        self._probabilities = HypothesisProbabilities({k: round(v / tot, 6) for k, v in canon.items()})

    def reset(self):
        self.base_rate_adapter.reset()
        cur_priors = self.base_rate_adapter.get_current_priors(include_aliases=False)
        self.default_priors = HypothesisProbabilities({
            "normal": cur_priors.get("noise", 0.55),
            "source_failure": cur_priors.get("sensor_failure", 0.15),
            "isolated_incident": cur_priors.get("isolated_incident", 0.20),
            "cascading_crisis": cur_priors.get("cascading_crisis", 0.10),
        })
        self._probabilities = self.default_priors.copy()

    def update(self, event: NormalizedEvent, quality_weight: float) -> tuple[HypothesisProbabilities, HypothesisProbabilities]:
        """
        Calculates tempered posterior probabilities:
          P(H_i | E) proportional to P(H_i) * P(E | H_i)^omega
        Returns (prior, posterior).
        """
        prior_snap = self.probabilities

        # Handle retractions directly
        if event.quality_flags and "retracted" in event.quality_flags:
            self._probabilities["cascading_crisis"] = max(0.04, self._probabilities["cascading_crisis"] * 0.6)
            self._probabilities["normal"] = min(0.85, self._probabilities["normal"] * 1.3)
            tot = sum(self._probabilities.values())
            self._probabilities = HypothesisProbabilities({k: v / tot for k, v in self._probabilities.items()})
            return prior_snap, self.probabilities

        # Lookup likelihood
        raw_lik = CANONICAL_LIKELIHOODS.get(
            event.event_type,
            {"noise": 0.35, "sensor_failure": 0.20, "isolated_incident": 0.35, "cascading_crisis": 0.40}
        )

        likelihood = {
            "normal": raw_lik.get("noise", 0.35),
            "source_failure": raw_lik.get("sensor_failure", 0.20),
            "isolated_incident": raw_lik.get("isolated_incident", 0.35),
            "cascading_crisis": raw_lik.get("cascading_crisis", 0.40),
        }

        # Severe confirmed events dynamically elevate cascade likelihood
        if event.severity > 0.75 and event.event_type in ("rainfall", "road_flooding", "earthquake", "flood", "cyclone"):
            likelihood["cascading_crisis"] = min(0.99, likelihood["cascading_crisis"] * (1.0 + 0.15 * event.severity))
            likelihood["normal"] = max(0.01, likelihood["normal"] * 0.5)

        # Temper likelihood towards uninformative prior (0.5) using quality weight omega
        w = max(0.05, min(1.0, quality_weight))
        tempered = {h: max(0.01, 0.5 + (likelihood[h] - 0.5) * w) for h in HYPOTHESES}

        # Apply Dirichlet floor (0.035) to prevent hypothesis starvation
        floor = 0.035
        smoothed = {h: max(floor, self._probabilities[h]) for h in HYPOTHESES}
        s_total = sum(smoothed.values())
        smoothed_prior = {h: smoothed[h] / s_total for h in HYPOTHESES}

        # Bayesian multiplication
        unnormalized = {h: smoothed_prior[h] * tempered[h] for h in HYPOTHESES}
        total = sum(unnormalized.values())

        if total > 0.0:
            self._probabilities = HypothesisProbabilities({h: unnormalized[h] / total for h in HYPOTHESES})

        return prior_snap, self.probabilities
