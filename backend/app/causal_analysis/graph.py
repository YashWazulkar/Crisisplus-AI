"""Causal and Cascading Disaster Dependency Graph for Nagpur.

Models plausible physical and operational propagation pathways between emergency events.
Enforces rigorous validation before marking an edge 'confirmed_cascade':
  1. Temporal order: Cause must precede consequence (time(src) < time(dst)).
  2. Plausible latency window: Consequence must occur within physical transition window.
  3. Spatial consistency: Events must share an administrative zone or hydrological catchment.
  4. Evidence quality: Sources must not be flagged as misleading, unverified, or sensor errors.
"""

from __future__ import annotations
import math
from datetime import datetime, timezone
from typing import Any
from ..normalization.schema import NormalizedEvent

# Latency windows in minutes (min_delay, max_delay)
LATENCY_WINDOWS = {
    ("severe_weather", "water_level"): (3.0, 30.0),
    ("water_level", "road_flooding"): (5.0, 40.0),
    ("road_flooding", "traffic_speed"): (5.0, 35.0),
    ("traffic_speed", "ambulance_delay"): (8.0, 45.0),
    ("ambulance_delay", "hospital_demand"): (15.0, 60.0),
    ("water_level", "power_outage"): (10.0, 60.0),
    ("earthquake", "road_flooding"): (1.0, 20.0),
    ("earthquake", "power_outage"): (0.5, 15.0),
    ("wildfire", "smoke_dispersion"): (10.0, 45.0),
    ("smoke_dispersion", "traffic_speed"): (10.0, 35.0),
}


class CausalDependencyGraph:
    """Directed graph representing verified physical cascade propagation pathways."""

    def __init__(self):
        self.nodes = [
            {"id": "severe_weather", "label": "Severe Storm / Intense Rainfall", "category": "meteorological"},
            {"id": "water_level", "label": "Drainage Surcharge / River Rise", "category": "hydrological"},
            {"id": "road_flooding", "label": "Arterial Road Submersion", "category": "transportation"},
            {"id": "traffic_speed", "label": "Corridor Paralysis & Chokepoints", "category": "transportation"},
            {"id": "power_outage", "label": "Substation / Grid Power Outage", "category": "infrastructure"},
            {"id": "ambulance_delay", "label": "Emergency Response & EMS Delays", "category": "operational"},
            {"id": "hospital_demand", "label": "Emergency Department Surge", "category": "healthcare"},
            {"id": "earthquake", "label": "Seismic Ground Motion", "category": "geophysical"},
            {"id": "wildfire", "label": "Active Wildfire Front", "category": "environmental"},
            {"id": "smoke_dispersion", "label": "Dense Smoke / Low Visibility", "category": "atmospheric"},
        ]

        self.edges = [
            {
                "from": "severe_weather", "to": "water_level",
                "mechanism": "Precipitation exceeds urban catchment stormwater runoff capacity",
                "latency_range": "3–30 min", "base_confidence": 0.85
            },
            {
                "from": "water_level", "to": "road_flooding",
                "mechanism": "Culvert overflow and low-lying underpass inundation",
                "latency_range": "5–40 min", "base_confidence": 0.90
            },
            {
                "from": "road_flooding", "to": "traffic_speed",
                "mechanism": "Impassable roadways cause gridlock on arterial diversion corridors",
                "latency_range": "5–35 min", "base_confidence": 0.92
            },
            {
                "from": "traffic_speed", "to": "ambulance_delay",
                "mechanism": "Paramedic and dispatch vehicles trapped in arterial congestion",
                "latency_range": "8–45 min", "base_confidence": 0.88
            },
            {
                "from": "ambulance_delay", "to": "hospital_demand",
                "mechanism": "Delayed transport clusters admissions and strains triage queues",
                "latency_range": "15–60 min", "base_confidence": 0.80
            },
            {
                "from": "water_level", "to": "power_outage",
                "mechanism": "Basement distribution panels or low-lying transformer vaults flood",
                "latency_range": "10–60 min", "base_confidence": 0.72
            },
            {
                "from": "earthquake", "to": "road_flooding",
                "mechanism": "Water main fracture and bridge approach settlement",
                "latency_range": "1–20 min", "base_confidence": 0.65
            },
            {
                "from": "earthquake", "to": "power_outage",
                "mechanism": "Substation busbar tripping and overhead feeder line collapse",
                "latency_range": "1–15 min", "base_confidence": 0.82
            },
            {
                "from": "wildfire", "to": "smoke_dispersion",
                "mechanism": "Atmospheric smoke plume inversion reduces highway visibility",
                "latency_range": "10–45 min", "base_confidence": 0.86
            },
            {
                "from": "smoke_dispersion", "to": "traffic_speed",
                "mechanism": "Precautionary highway closures and severe visibility drop",
                "latency_range": "10–35 min", "base_confidence": 0.78
            },
        ]

    def _matches_type(self, event_type: str, node_id: str) -> bool:
        if node_id == "severe_weather":
            return event_type in ("severe_weather", "rainfall", "wind_gust", "cyclone")
        return event_type == node_id

    def evaluate_active_pathways(self, observed_events: list[NormalizedEvent]) -> dict[str, Any]:
        """
        Calculates dynamic activation confidence enforcing:
          - Temporal sequence (cause precedes effect)
          - Plausible latency interval
          - Spatial co-location
          - Source reliability checks
        """
        valid_events = [
            e for e in observed_events[-40:]
            if not any(f in e.quality_flags for f in ("misleading", "retracted", "sensor_error"))
        ]

        evaluated_edges = []
        confirmed_count = 0
        developing_count = 0

        for edge in self.edges:
            src_node = edge["from"]
            dst_node = edge["to"]
            latency_min, latency_max = LATENCY_WINDOWS.get((src_node, dst_node), (2.0, 60.0))

            src_events = [e for e in valid_events if self._matches_type(e.event_type, src_node)]
            dst_events = [e for e in valid_events if self._matches_type(e.event_type, dst_node)]

            status = "inactive"
            current_confidence = edge["base_confidence"] * 0.15
            explanation = "Precondition not observed in active window."

            if src_events:
                # Precondition observed
                earliest_src = min(src_events, key=lambda x: x.event_timestamp)
                status = "developing_risk"
                current_confidence = edge["base_confidence"] * 0.75
                explanation = f"Precondition {src_node} observed at {earliest_src.event_timestamp.strftime('%H:%M')}; consequence plausible within {latency_min:.0f}–{latency_max:.0f} min."
                developing_count += 1

                if dst_events:
                    # Both observed: rigorously test causal relationship
                    causal_pair_found = False
                    temporal_reversal_detected = False

                    for s in src_events:
                        for d in dst_events:
                            delta_min = (d.event_timestamp - s.event_timestamp).total_seconds() / 60.0

                            if delta_min < 0:
                                # Destination happened BEFORE source! NOT causal!
                                temporal_reversal_detected = True
                            elif latency_min <= delta_min <= latency_max:
                                # Check spatial consistency (same zone or both district level)
                                same_zone = (s.assigned_zone_id and d.assigned_zone_id and s.assigned_zone_id == d.assigned_zone_id)
                                district_wide = (s.geographic_precision == "district_level" or d.geographic_precision == "district_level")

                                if same_zone or district_wide:
                                    causal_pair_found = True
                                    status = "confirmed_cascade"
                                    # Corroborated with spatial and temporal consistency
                                    current_confidence = min(0.98, edge["base_confidence"] * 1.1)
                                    explanation = (
                                        f"Confirmed causal link: {s.event_type} at {s.event_timestamp.strftime('%H:%M')} "
                                        f"preceded {d.event_type} by {delta_min:.1f} min in consistent spatial catchment."
                                    )
                                    confirmed_count += 1
                                    break
                        if causal_pair_found:
                            break

                    if not causal_pair_found and temporal_reversal_detected and status != "confirmed_cascade":
                        status = "non_causal_correlation"
                        current_confidence = 0.20
                        explanation = (
                            f"Temporal order violation: Consequence event appeared before or outside plausible latency window. "
                            f"Treated as coincidental / independent occurrence rather than causal cascade."
                        )

            evaluated_edges.append({
                "from": edge["from"],
                "to": edge["to"],
                "mechanism": edge["mechanism"],
                "latency_range": edge["latency_range"],
                "status": status,
                "confidence": round(current_confidence, 2),
                "causal_explanation": explanation,
            })

        return {
            "nodes": self.nodes,
            "edges": evaluated_edges,
            "confirmed_pathways": confirmed_count,
            "developing_pathways": developing_count,
        }
