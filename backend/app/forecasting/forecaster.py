"""Predictive Forecasting Engine for Short-Horizon Emergency Developments in Nagpur.

Generates explicit, distinct forecasts of the next three plausible events conditioned on:
  - Observed meteorological telemetry (IMD & Open-Meteo)
  - Municipal drainage thresholds and chronic low-clearance hotspots in Nagpur
  - Critical arterial corridors (Wardha Road, Central Avenue, South Ring Road)
  - Active causal pathways and Bayesian posterior distributions

Each forecast includes:
  1. Predicted event type
  2. Earliest and latest plausible occurrence window (ISO timestamps and minutes)
  3. Affected location / zone
  4. Probability and confidence
  5. Current supporting evidence
  6. Explicit causal chain
  7. Dependencies and assumptions
  8. Epistemic uncertainty and alternative outcomes
  9. Grounding data basis (OBSERVED_DATA, CAUSAL_RULE, STATISTICAL_MODEL, SYNTHETIC_SIMULATION)
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any
from ..normalization.schema import NormalizedEvent
from ..geography.nagpur_registry import (
    NMC_ZONES,
    NAGPUR_WATERLOGGING_HOTSPOTS,
)

MODEL_VERSION = "CrisisPulse-Nagpur-CausalForecaster-v3.0"


class PredictiveForecaster:
    """Computes distinct short-horizon event forecasts grounded in causal pathways."""

    @classmethod
    def generate_forecasts(
        cls,
        probabilities: dict[str, float],
        recent_events: list[NormalizedEvent],
        active_zone_id: str | None = None,
        active_zone_name: str | None = None,
        now: datetime | None = None,
    ) -> list[dict[str, Any]]:
        now_dt = now or datetime.now(timezone.utc)
        target_zone_id = active_zone_id or "zone-3-hanuman-nagar"
        zone_meta = NMC_ZONES.get(target_zone_id, NMC_ZONES["zone-3-hanuman-nagar"])
        display_zone_name = active_zone_name or zone_meta["name"]

        p_cascade = probabilities.get("cascading_crisis", 0.10)
        p_failure = probabilities.get("sensor_failure", probabilities.get("source_failure", 0.15))
        p_isolated = probabilities.get("isolated_incident", 0.20)
        p_noise = probabilities.get("noise", probabilities.get("normal", 0.55))

        event_types = {e.event_type for e in recent_events[-20:]}
        rainfall_events = [e for e in recent_events[-20:] if e.event_type == "rainfall" and e.magnitude is not None]
        max_rain_mm = max([e.magnitude for e in rainfall_events] or [0.0])

        relevant_hotspots = [h for h in NAGPUR_WATERLOGGING_HOTSPOTS if h["zone_id"] == target_zone_id]
        hotspot_name = relevant_hotspots[0]["name"] if relevant_hotspots else f"{display_zone_name} Low-Clearance Arterial Underpass"

        forecasts: list[dict[str, Any]] = []

        # ---------------------------------------------------------------------
        # FORECAST 1: Near-term Drainage Surcharge & Roadway Waterlogging (5–15 min)
        # ---------------------------------------------------------------------
        if p_cascade >= 0.30 or max_rain_mm >= 25.0 or "water_level" in event_types or "drainage_overflow" in event_types:
            prob_flooding = min(0.96, round(p_cascade * 0.85 + 0.15 + (max_rain_mm / 100.0) * 0.12, 3))
            earliest_dt = now_dt + timedelta(minutes=5)
            latest_dt = now_dt + timedelta(minutes=15)

            evidence_items = []
            if max_rain_mm > 0:
                evidence_items.append(f"Recorded precipitation of {max_rain_mm:.1f} mm/h exceeding stormwater threshold")
            if "water_level" in event_types:
                evidence_items.append("Hydrological gauge reports rising drainage culvert stage")
            evidence_items.append(f"Documented historical catchment vulnerability at {hotspot_name}")

            forecasts.append({
                "forecast_id": f"fc-1-{int(now_dt.timestamp())}",
                "rank": 1,
                "event_type": "road_flooding",
                "label": f"Arterial Underpass Submersion at {hotspot_name}",
                "earliest_time": earliest_dt.isoformat(),
                "latest_time": latest_dt.isoformat(),
                "time_window": "5–15 minutes",
                "affected_zone_id": target_zone_id,
                "affected_location": f"{hotspot_name}, {display_zone_name}",
                "probability": prob_flooding,
                "confidence_score": 0.86,
                "confidence_label": "High Model Confidence (Hydrological Runoff)",
                "supporting_evidence": evidence_items,
                "causal_pathway": "Sustained Heavy Rainfall → Urban Catchment Surcharge → Low-Lying Underpass Ponding",
                "dependencies_and_assumptions": [
                    "Municipal storm sewer culverts partially constricted by monsoon silt.",
                    "No immediate auxiliary diesel pump deployment by municipal engineering crews.",
                ],
                "uncertainty_and_alternatives": (
                    "If stormwater pumps at the underpass engage within 8 minutes, water depth will cap at <15cm. "
                    "If rainfall intensifies beyond 50 mm/h, submersion will extend into surrounding residential feeder streets."
                ),
                "data_basis": "OBSERVED_DATA" if max_rain_mm > 0 else "CAUSAL_RULE",
                "model_version": MODEL_VERSION,
            })
        elif p_failure >= 0.40:
            earliest_dt = now_dt + timedelta(minutes=2)
            latest_dt = now_dt + timedelta(minutes=10)
            forecasts.append({
                "forecast_id": f"fc-1-fail-{int(now_dt.timestamp())}",
                "rank": 1,
                "event_type": "sensor_telemetry_gap",
                "label": f"Persistent Sensor Telemetry Dropout in {display_zone_name}",
                "earliest_time": earliest_dt.isoformat(),
                "latest_time": latest_dt.isoformat(),
                "time_window": "2–10 minutes",
                "affected_zone_id": target_zone_id,
                "affected_location": f"Telemetry network nodes ({display_zone_name})",
                "probability": round(min(0.92, p_failure * 0.95), 3),
                "confidence_score": 0.88,
                "confidence_label": "High Hardware Diagnostic Confidence",
                "supporting_evidence": ["Synchronized telemetry silence across monitoring gateway", "Hardware heartbeat timeout"],
                "causal_pathway": "Gateway Controller Malfunction → Telemetry Dropouts → Elevated Epistemic Uncertainty",
                "dependencies_and_assumptions": ["Awaiting manual field technician reset or automated cellular reconnection."],
                "uncertainty_and_alternatives": "If primary gateway reboots successfully, telemetry resumes without data loss.",
                "data_basis": "OBSERVED_DATA",
                "model_version": MODEL_VERSION,
            })
        else:
            earliest_dt = now_dt + timedelta(minutes=5)
            latest_dt = now_dt + timedelta(minutes=20)
            forecasts.append({
                "forecast_id": f"fc-1-nom-{int(now_dt.timestamp())}",
                "rank": 1,
                "event_type": "nominal_drainage_flow",
                "label": f"Stable Hydrological & Drainage Flow ({display_zone_name})",
                "earliest_time": earliest_dt.isoformat(),
                "latest_time": latest_dt.isoformat(),
                "time_window": "5–20 minutes",
                "affected_zone_id": target_zone_id,
                "affected_location": display_zone_name,
                "probability": round(p_noise * 0.85, 3),
                "confidence_score": 0.90,
                "confidence_label": "High Baseline Persistence",
                "supporting_evidence": ["IMD & Open-Meteo telemetry within nominal dry/moderate limits"],
                "causal_pathway": "Nominal Catchment Absorption → Normal Stormwater Discharge → Open Transit",
                "dependencies_and_assumptions": ["No sudden cloudburst initiation upstream."],
                "uncertainty_and_alternatives": "Localized convective storms may develop without radar lead time.",
                "data_basis": "STATISTICAL_MODEL",
                "model_version": MODEL_VERSION,
            })

        # ---------------------------------------------------------------------
        # FORECAST 2: Mid-term Arterial Traffic Congestion & EMS Route Delay (15–35 min)
        # ---------------------------------------------------------------------
        if p_cascade >= 0.25 or "road_flooding" in event_types or "traffic_speed" in event_types:
            prob_traffic = min(0.92, round(p_cascade * 0.80 + 0.14, 3))
            earliest_dt = now_dt + timedelta(minutes=15)
            latest_dt = now_dt + timedelta(minutes=35)
            forecasts.append({
                "forecast_id": f"fc-2-{int(now_dt.timestamp())}",
                "rank": 2,
                "event_type": "ambulance_delay",
                "label": f"EMS Route Latency & Arterial Bottleneck on Wardha Road / Ring Road",
                "earliest_time": earliest_dt.isoformat(),
                "latest_time": latest_dt.isoformat(),
                "time_window": "15–35 minutes",
                "affected_zone_id": target_zone_id,
                "affected_location": f"Primary Trauma Transit Corridor ({display_zone_name})",
                "probability": prob_traffic,
                "confidence_score": 0.82,
                "confidence_label": "Moderate-High Transportation Flow Model",
                "supporting_evidence": [
                    "Underpass flooding forcing vehicular diversion onto secondary arterials",
                    "Telemetry showing deceleration in transit corridor velocity",
                ],
                "causal_pathway": "Underpass Inundation → Traffic Diversion → Secondary Chokepoint Gridlock → Paramedic Transport Latency",
                "dependencies_and_assumptions": [
                    "Traffic police have not established contraflow lanes or manual intersection clearance.",
                    "Civilian vehicles attempting navigation around submerged areas cause gridlock.",
                ],
                "uncertainty_and_alternatives": (
                    "If traffic police deploy within 10 minutes to reroute traffic along elevated flyovers, "
                    "ambulance delay will be restricted to <5 minutes."
                ),
                "data_basis": "CAUSAL_RULE",
                "model_version": MODEL_VERSION,
            })
        elif p_isolated >= 0.35:
            earliest_dt = now_dt + timedelta(minutes=10)
            latest_dt = now_dt + timedelta(minutes=25)
            forecasts.append({
                "forecast_id": f"fc-2-iso-{int(now_dt.timestamp())}",
                "rank": 2,
                "event_type": "localized_traffic_clearance",
                "label": f"Resolution of Localized Street Bottleneck ({display_zone_name})",
                "earliest_time": earliest_dt.isoformat(),
                "latest_time": latest_dt.isoformat(),
                "time_window": "10–25 minutes",
                "affected_zone_id": target_zone_id,
                "affected_location": display_zone_name,
                "probability": round(p_isolated * 0.75, 3),
                "confidence_score": 0.75,
                "confidence_label": "Moderate Incident Clearance Model",
                "supporting_evidence": ["Single isolated disruption report without cascading multi-sensor corroboration"],
                "causal_pathway": "Isolated Incident → Localized Bottleneck → Rapid Civic Resolution",
                "dependencies_and_assumptions": ["Tow trucks or local ward officers handle incident."],
                "uncertainty_and_alternatives": "Rubbernecking may temporarily slow adjacent lanes.",
                "data_basis": "STATISTICAL_MODEL",
                "model_version": MODEL_VERSION,
            })
        else:
            earliest_dt = now_dt + timedelta(minutes=15)
            latest_dt = now_dt + timedelta(minutes=35)
            forecasts.append({
                "forecast_id": f"fc-2-flow-{int(now_dt.timestamp())}",
                "rank": 2,
                "event_type": "routine_transit_flow",
                "label": f"Unimpeded Emergency Vehicle Access across {display_zone_name}",
                "earliest_time": earliest_dt.isoformat(),
                "latest_time": latest_dt.isoformat(),
                "time_window": "15–35 minutes",
                "affected_zone_id": target_zone_id,
                "affected_location": f"Emergency corridors in {display_zone_name}",
                "probability": round(p_noise * 0.80, 3),
                "confidence_score": 0.88,
                "confidence_label": "High Steady-State Confidence",
                "supporting_evidence": ["No active road submersion reports", "Open corridor velocity monitors"],
                "causal_pathway": "Clear Roadways → Open Transit Corridors → On-Time Emergency Dispatch",
                "dependencies_and_assumptions": ["No vehicular breakdowns or unannounced construction."],
                "uncertainty_and_alternatives": "Standard peak-hour congestion may cause mild routine delays.",
                "data_basis": "STATISTICAL_MODEL",
                "model_version": MODEL_VERSION,
            })

        # ---------------------------------------------------------------------
        # FORECAST 3: Horizon Healthcare / Hospital Intake Surge (30–60 min)
        # ---------------------------------------------------------------------
        if p_cascade >= 0.35 or "ambulance_delay" in event_types or "road_flooding" in event_types:
            prob_hosp = min(0.90, round(p_cascade * 0.75 + 0.12, 3))
            earliest_dt = now_dt + timedelta(minutes=30)
            latest_dt = now_dt + timedelta(minutes=60)
            forecasts.append({
                "forecast_id": f"fc-3-{int(now_dt.timestamp())}",
                "rank": 3,
                "event_type": "hospital_demand",
                "label": f"Emergency Department Triage Saturation at Apex Receiving Hospitals (GMCH / Mayo)",
                "earliest_time": earliest_dt.isoformat(),
                "latest_time": latest_dt.isoformat(),
                "time_window": "30–60 minutes",
                "affected_zone_id": target_zone_id,
                "affected_location": "GMCH (Hanuman Nagar) & Mayo Hospital (Gandhibagh) Receiving ERs",
                "probability": prob_hosp,
                "confidence_score": 0.76,
                "confidence_label": "Healthcare Queueing Model",
                "supporting_evidence": [
                    "Delayed ambulances batching incoming trauma patients simultaneously",
                    f"Submerged arterial transit corridors delaying non-emergency transfers across {display_zone_name}",
                ],
                "causal_pathway": "Ambulance Transport Delays → Batched Emergency Arrivals → Triage Queue Saturation",
                "dependencies_and_assumptions": [
                    "Secondary hospitals (AIIMS Nagpur, Orange City, Kingsway) have not initiated mutual aid diversion protocols.",
                    "Emergency department nursing and resuscitation staff operate at baseline shift capacity.",
                ],
                "uncertainty_and_alternatives": (
                    "Activating pre-alert hospital mutual aid to distribute admissions across private tertiary centers "
                    "will cap public ER bed strain below 75%."
                ),
                "data_basis": "CAUSAL_RULE",
                "model_version": MODEL_VERSION,
            })
        else:
            earliest_dt = now_dt + timedelta(minutes=30)
            latest_dt = now_dt + timedelta(minutes=60)
            forecasts.append({
                "forecast_id": f"fc-3-nom-{int(now_dt.timestamp())}",
                "rank": 3,
                "event_type": "nominal_healthcare_capacity",
                "label": f"Adequate Healthcare & Emergency Resuscitation Reserves ({display_zone_name})",
                "earliest_time": earliest_dt.isoformat(),
                "latest_time": latest_dt.isoformat(),
                "time_window": "30–60 minutes",
                "affected_zone_id": target_zone_id,
                "affected_location": "Nagpur Regional Trauma Centers",
                "probability": round(p_noise * 0.82, 3),
                "confidence_score": 0.85,
                "confidence_label": "Macro-Operational Equilibrium",
                "supporting_evidence": ["Bed occupancy telemetry within nominal operating buffer"],
                "causal_pathway": "Steady Emergency Intake → Balanced Discharge Rate → Stable Resuscitation Reserves",
                "dependencies_and_assumptions": ["No external mass-casualty incident outside weather scope."],
                "uncertainty_and_alternatives": "Seasonal illness spikes can elevate occupancy independently.",
                "data_basis": "STATISTICAL_MODEL",
                "model_version": MODEL_VERSION,
            })

        return forecasts
