"""Anomaly Detection Engine for Numerical Telemetry and Spatial Clustering.

Implements robust Z-scores via Median Absolute Deviation (MAD), change-point detection,
and spatial event concentration analysis to detect statistical anomalies.
"""

from __future__ import annotations
import math
import statistics
from collections import deque
from datetime import datetime, timezone
from typing import Any
from ..normalization.schema import NormalizedEvent
from ..deduplication.deduplicator import haversine_distance_km

class AnomalyResult:
    def __init__(self, is_anomaly: bool, score: float, metric_name: str, explanation: str, anomaly_type: str):
        self.is_anomaly = is_anomaly
        self.score = score  # Robust Z-score or concentration index
        self.metric_name = metric_name
        self.explanation = explanation
        self.anomaly_type = anomaly_type

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_anomaly": self.is_anomaly,
            "score": round(self.score, 2),
            "metric_name": self.metric_name,
            "explanation": self.explanation,
            "anomaly_type": self.anomaly_type,
        }

class AnomalyDetector:
    """Tracks sliding baseline windows and flags anomalous spikes and geographic swarms."""

    def __init__(self, history_len: int = 100):
        # Rolling baseline buffers by metric
        self.rainfall_history: deque[float] = deque(maxlen=history_len)
        self.wind_history: deque[float] = deque(maxlen=history_len)
        self.seismic_history: deque[float] = deque(maxlen=history_len)
        self.recent_events: deque[NormalizedEvent] = deque(maxlen=history_len)

    def reset(self):
        self.rainfall_history.clear()
        self.wind_history.clear()
        self.seismic_history.clear()
        self.recent_events.clear()

    @staticmethod
    def compute_robust_z(val: float, history: list[float]) -> float:
        """Calculates robust Z-score using Median and Median Absolute Deviation (MAD)."""
        if len(history) < 5:
            return 0.0
        med = statistics.median(history)
        deviations = [abs(x - med) for x in history]
        mad = statistics.median(deviations)
        if mad < 1e-4:
            # Handle near-zero variance gracefully
            stdev = statistics.pstdev(history) if len(history) > 1 else 0.0
            return (val - med) / (stdev + 1e-3)
        return (val - med) / (1.4826 * mad)

    def evaluate(self, event: NormalizedEvent) -> list[AnomalyResult]:
        anomalies: list[AnomalyResult] = []
        self.recent_events.append(event)

        # 1. Numerical time-series anomaly detection (Rainfall)
        if event.event_type == "rainfall" and event.magnitude is not None:
            z = self.compute_robust_z(event.magnitude, list(self.rainfall_history))
            self.rainfall_history.append(event.magnitude)
            if z >= 3.0 and event.magnitude >= 15.0:
                anomalies.append(
                    AnomalyResult(
                        is_anomaly=True,
                        score=z,
                        metric_name="precipitation_burst",
                        explanation=f"Rainfall rate {event.magnitude:.1f} mm/h is {z:.1f} MAD standard deviations above local baseline.",
                        anomaly_type="statistical_time_series_spike",
                    )
                )

        # 2. Wind Gust Anomaly
        if event.event_type == "wind_gust" and event.magnitude is not None:
            z = self.compute_robust_z(event.magnitude, list(self.wind_history))
            self.wind_history.append(event.magnitude)
            if z >= 2.5 and event.magnitude >= 50.0:
                anomalies.append(
                    AnomalyResult(
                        is_anomaly=True,
                        score=z,
                        metric_name="extreme_wind_gust",
                        explanation=f"Wind gust of {event.magnitude:.1f} km/h represents a sudden velocity acceleration (Z={z:.1f}).",
                        anomaly_type="statistical_time_series_spike",
                    )
                )

        # 3. Seismic Magnitude Anomaly
        if event.event_type == "earthquake" and event.magnitude is not None:
            z = self.compute_robust_z(event.magnitude, list(self.seismic_history))
            self.seismic_history.append(event.magnitude)
            if event.magnitude >= 5.5:
                anomalies.append(
                    AnomalyResult(
                        is_anomaly=True,
                        score=max(z, (event.magnitude - 4.0) * 1.5),
                        metric_name="major_seismic_shock",
                        explanation=f"Magnitude M{event.magnitude:.1f} exceeds regional baseline threshold.",
                        anomaly_type="extreme_value_observation",
                    )
                )

        # 4. Spatial Clustering / Geographic Concentration
        # Count recent events within 30km in the last 30 minutes
        cluster_count = 0
        now_time = event.event_timestamp
        for other in self.recent_events:
            if other.event_id == event.event_id:
                continue
            time_diff = abs((now_time - other.event_timestamp).total_seconds())
            if time_diff <= 1800:  # 30 minutes
                dist = haversine_distance_km(event.latitude, event.longitude, other.latitude, other.longitude)
                if dist <= 35.0:
                    cluster_count += 1

        if cluster_count >= 3:
            anomalies.append(
                AnomalyResult(
                    is_anomaly=True,
                    score=float(cluster_count),
                    metric_name="spatial_cluster_swarm",
                    explanation=f"Geographic concentration detected: {cluster_count + 1} incidents co-located within 35 km in a 30-minute window.",
                    anomaly_type="spatial_density_anomaly",
                )
            )

        return anomalies
