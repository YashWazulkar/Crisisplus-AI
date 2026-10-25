"""Scenario Generator and Adversarial Stress Testing Engine for Nagpur Emergency Intelligence.

Provides deterministic, reproducible synthetic and historical replay streams for:
  - The Twin Test (A vs B sharing identical minutes 0–6, diverging at minute 7)
  - 16 Comprehensive Adversarial Scenarios addressing sensor outages, common-cause failures,
    coordinated rumors, delayed messages, retractions, stream cutouts, and base-rate shifts.
"""

from __future__ import annotations
import random
from datetime import datetime, timedelta, timezone
from typing import Any
from .schemas import Event

# Full registry of all 16 standardized operational and stress scenarios
SCENARIOS = {
    # Central Challenge Twin Benchmarks
    "twin_a": "Twin Test A — Genuine Cascading Crisis (Nagpur)",
    "twin_b": "Twin Test B — Sensor/Gateway Failure Look-alike (Nagpur)",

    # Core Challenge Benchmark Scenarios
    "cascade": "1. Genuine Cascading Crisis (Multi-sector cascade)",
    "heavy_rain_no_cascade": "2. Heavy Rain Without Cascading Emergency (High drainage absorption)",
    "isolated_flooding": "3. Isolated Road-Flooding Incident (Localized underpass blockage)",
    "hospital_flu_cluster": "4. Hospital Flu Cluster Unrelated to Weather (Seasonal OPD spike)",
    "gateway_masking_100": "5. One Gateway Masking 100 Sensors (Synchronized telemetry drop)",
    "stale_repeated_sensors": "6. Stale and Repeated Sensor Values (Frozen hardware gauges)",
    "camera_cutout": "7. Mid-Episode Camera / Stream Cutout (Sudden sensor loss during storm)",
    "delayed_dispatch": "8. Delayed Emergency Dispatch Logs (Out-of-order latency)",
    "out_of_order_stream": "9. Duplicate and Out-of-Order Reports (Network jitter & replays)",
    "event_retractions": "10. Event Retractions and Corrected Measurements (Sensor recalibration)",
    "coordinated_rumors": "11. Coordinated Rumor Waves & Social Bursts (Uncorroborated panic)",
    "contradictory_reports": "12. Contradictory Official vs Unverified Citizen Reports",
    "simultaneous_unrelated": "13. Multiple Unrelated Events Occurring Simultaneously (Fire + Traffic)",
    "emergency_with_outage": "14. Real Emergency Coinciding With Partial Source Outage",
    "seasonal_base_rate_drift": "15. Seasonal Base-Rate Drift (Monsoon onset baseline shift)",
    "rapid_escalation": "16. Rapidly Deteriorating Cloudburst (Urgent zero-latency escalation)",

    # Backward compatibility aliases
    "sensor_failure": "5. Sensor / Gateway Failure",
    "isolated": "3. Isolated Road Incident",
    "normal": "2. Normal Storm",
    "misleading": "11. Coordinated Misleading Reports",
    "stream_cutout": "7. Stream Cutout During Incident",
}

DEFAULT_NAGPUR_ZONE = "zone-3-hanuman-nagar"
DEFAULT_NAGPUR_ZONE_NAME = "Hanuman Nagar Zone"


def make_scenario_events(name: str, seed: int = 42) -> list[Event]:
    """
    Constructs a deterministic sequence of timestamped events for the specified scenario.
    All events respect Nagpur District geography and NMC municipal zones.
    """
    rng = random.Random(seed)
    # Fixed base timestamp for deterministic time calculation across replays
    base_time = datetime(2026, 10, 25, 12, 0, 0, tzinfo=timezone.utc)
    specs: list[tuple[int, str, str, float, float, str, str | None, dict[str, Any], list[str], str]] = []

    def add(
        minute: int,
        typ: str,
        source: str,
        severity: float,
        reliability: float = 0.85,
        zone: str = DEFAULT_NAGPUR_ZONE_NAME,
        gateway: str | None = None,
        payload: dict[str, Any] | None = None,
        flags: list[str] | None = None,
        event_id_override: str | None = None,
    ):
        eid = event_id_override or f"{name}-{seed}-{len(specs)}"
        specs.append((minute, typ, source, severity, reliability, zone, gateway, payload or {}, flags or [], eid))

    # =========================================================================
    # THE TWIN TEST: Strict identical prefix for Minutes 0–6
    # =========================================================================
    if name in ("twin_a", "twin_b"):
        # Minutes 0 to 6 MUST BE 100% BIT-FOR-BIT IDENTICAL in both twins
        # Evidence is ambiguous: weather worsening, traffic slowing, but NO multi-source confirmed cascade yet.
        shared_prefix = [
            (0, "rainfall", "weather-station-nagpur", 0.45, 0.96, DEFAULT_NAGPUR_ZONE_NAME, None, {"rain_mm_h": 22.0}, []),
            (1, "traffic_speed", "itms-traffic-wardha-rd", 0.38, 0.90, DEFAULT_NAGPUR_ZONE_NAME, "traffic-gw-south", {"speed_kmh": 36.0}, []),
            (2, "water_level", "nmc-drainage-culvert-01", 0.45, 0.88, DEFAULT_NAGPUR_ZONE_NAME, "water-gw-hanuman", {"water_stage_m": 0.9}, ["single_sensor"]),
            (3, "rainfall", "weather-station-nagpur", 0.50, 0.96, DEFAULT_NAGPUR_ZONE_NAME, None, {"rain_mm_h": 32.0}, []),
            (4, "traffic_speed", "itms-traffic-ring-rd", 0.48, 0.90, DEFAULT_NAGPUR_ZONE_NAME, "traffic-gw-south", {"speed_kmh": 28.0}, []),
            (5, "water_level", "nmc-drainage-culvert-02", 0.50, 0.88, DEFAULT_NAGPUR_ZONE_NAME, "water-gw-hanuman", {"water_stage_m": 1.2}, ["single_sensor"]),
            (6, "citizen_report", "nagpur-civic-app-01", 0.45, 0.65, DEFAULT_NAGPUR_ZONE_NAME, None, {"report_text": "Water ponding near underpass"}, ["unverified"]),
        ]

        # Ingest identical shared prefix with SHARED event IDs
        for row in shared_prefix:
            shared_id = f"twin-shared-{seed}-m{row[0]}"
            add(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], event_id_override=shared_id)

        # Minute 7+: DIVIDED PATHWAYS
        if name == "twin_a":
            # Twin A — Genuine Cascade: Corroborated ground truth multi-source disaster
            add(7, "road_flooding", "traffic-police-nagpur", 0.91, 0.96, DEFAULT_NAGPUR_ZONE_NAME, None, {"corroborated": True, "water_depth_cm": 65}, ["ground_verified"])
            add(8, "ambulance_delay", "108-ems-dispatch", 0.84, 0.94, DEFAULT_NAGPUR_ZONE_NAME, None, {"delay_min": 24, "corridor": "Wardha Road"})
            add(9, "hospital_demand", "gmch-emergency-triage", 0.79, 0.92, DEFAULT_NAGPUR_ZONE_NAME, None, {"bed_occupancy_pct": 92.0})
            add(10, "power_outage", "msedcl-substation-feeder", 0.85, 0.95, DEFAULT_NAGPUR_ZONE_NAME, "power-gw-central", {"substation": "Medical Square"})
        else:
            # Twin B — False Cascade: Corrupted gateway failure, hardware glitch, and rumors
            add(7, "gateway_failure", "water-gw-hanuman", 0.96, 0.98, DEFAULT_NAGPUR_ZONE_NAME, "water-gw-hanuman", {"status": "controller_timeout", "reason": "Loss of gateway mains power"})
            add(8, "sensor_failure", "nmc-drainage-culvert-01", 0.92, 0.90, DEFAULT_NAGPUR_ZONE_NAME, "water-gw-hanuman", {"error": "stale_repeated_telemetry"})
            add(9, "citizen_report", "social-rumor-burst", 0.88, 0.22, DEFAULT_NAGPUR_ZONE_NAME, None, {"misleading": True, "claim": "Dam burst upstream"}, ["unverified", "coordinated", "misleading"])
            add(10, "source_recovered", "water-gw-hanuman", 0.30, 0.95, DEFAULT_NAGPUR_ZONE_NAME, "water-gw-hanuman", {"status": "reboot_successful", "telemetry": "drainage_normal"})

    # =========================================================================
    # 16 ADVERSARIAL & OPERATIONAL SCENARIOS
    # =========================================================================
    elif name == "cascade":
        add(0, "rainfall", "weather-station-nagpur", 0.70, 0.96, payload={"rain_mm_h": 55.0})
        add(1, "water_level", "nmc-drainage-culvert-01", 0.72, 0.90, gateway="water-gw")
        add(2, "traffic_speed", "itms-traffic-01", 0.68, 0.92, gateway="traffic-gw")
        add(3, "water_level", "nmc-drainage-culvert-02", 0.85, 0.91, gateway="water-gw")
        add(4, "road_flooding", "traffic-police-eoc", 0.92, 0.96, flags=["ground_verified"])
        add(5, "ambulance_delay", "108-ems-dispatch", 0.82, 0.94)
        add(6, "hospital_demand", "gmch-emergency-triage", 0.78, 0.92)
        add(7, "road_flooding", "traffic-police-eoc", 0.94, 0.96, flags=["ground_verified"])
        add(8, "ambulance_delay", "108-ems-dispatch", 0.88, 0.94)
        add(9, "hospital_demand", "mayo-emergency-triage", 0.84, 0.92)

    elif name in ("heavy_rain_no_cascade", "normal"):
        # High rainfall but municipal drainage handles it without systemic cascade
        add(0, "rainfall", "weather-station-nagpur", 0.65, 0.96, payload={"rain_mm_h": 40.0})
        add(2, "traffic_speed", "itms-traffic-01", 0.38, 0.90, gateway="traffic-gw")
        add(4, "rainfall", "weather-station-nagpur", 0.50, 0.96, payload={"rain_mm_h": 25.0})
        add(6, "water_level", "nmc-drainage-culvert-01", 0.35, 0.90, gateway="water-gw", payload={"water_stage_m": 0.8})
        add(8, "traffic_speed", "itms-traffic-02", 0.30, 0.90, gateway="traffic-gw")

    elif name in ("isolated_flooding", "isolated"):
        # A water main breaks or localized puddle at one corner; arterial roads remain clear
        add(0, "traffic_speed", "itms-traffic-01", 0.45, 0.90)
        add(1, "citizen_report", "civic-app-01", 0.70, 0.75, payload={"text": "Water main fracture near corner"})
        add(3, "road_flooding", "ward-patrol-01", 0.60, 0.85, payload={"depth_cm": 15, "localized": True})
        add(5, "traffic_speed", "itms-traffic-01", 0.40, 0.90)

    elif name == "hospital_flu_cluster":
        # Hospital admissions spike due to seasonal viral fever, NOT flood or disaster
        add(0, "rainfall", "weather-station-nagpur", 0.15, 0.96, payload={"rain_mm_h": 0.0})
        add(2, "traffic_speed", "itms-traffic-01", 0.20, 0.90)
        add(4, "hospital_demand", "gmch-opd-intake", 0.82, 0.92, payload={"diagnosis": "seasonal_influenza_outpatient", "emergency_trauma_normal": True})
        add(6, "hospital_demand", "mayo-opd-intake", 0.78, 0.92, payload={"diagnosis": "seasonal_influenza_outpatient"})
        add(8, "ambulance_delay", "108-ems-dispatch", 0.25, 0.92, payload={"turnaround_normal": True})

    elif name in ("gateway_masking_100", "sensor_failure"):
        # 100 sensors behind 1 gateway: gateway trips, creating synchronized outage
        add(0, "rainfall", "weather-station-nagpur", 0.45, 0.96)
        add(1, "gateway_failure", "water-iot-concentrator-gw", 0.98, 0.98, gateway="water-gw", payload={"connected_sensors_count": 100})
        # Simulate burst of 5 representative sensors all dropping simultaneously
        for i in range(1, 6):
            add(2, "sensor_failure", f"drainage-sensor-{i:03d}", 0.95, 0.90, gateway="water-gw", flags=["gateway_correlated"])
        add(5, "traffic_speed", "itms-traffic-01", 0.35, 0.90, gateway="traffic-gw")

    elif name == "stale_repeated_sensors":
        # Gauges stick and repeat identical values across consecutive minutes
        add(0, "rainfall", "weather-station-nagpur", 0.50, 0.96, payload={"rain_mm_h": 22.0})
        for m in range(1, 6):
            add(m, "water_level", "nmc-frozen-gauge-01", 0.85, 0.80, gateway="water-gw", payload={"magnitude": 3.450}, flags=["repeated_value"])

    elif name in ("camera_cutout", "stream_cutout"):
        # Real storm begins, but midway through episode video stream completely cuts out
        add(0, "rainfall", "weather-station-nagpur", 0.65, 0.96, payload={"rain_mm_h": 48.0})
        add(1, "water_level", "nmc-drainage-culvert-01", 0.75, 0.90, gateway="water-gw")
        add(3, "gateway_failure", "cctv-optical-fiber-gateway", 0.96, 0.95, gateway="camera-gw", payload={"cutout": True})
        add(5, "ambulance_delay", "108-ems-dispatch", 0.78, 0.94)
        add(7, "hospital_demand", "gmch-emergency-triage", 0.72, 0.92)

    elif name == "delayed_dispatch":
        # Emergency call logs arrive with delayed event timestamps
        add(0, "rainfall", "weather-station-nagpur", 0.60, 0.96)
        add(2, "water_level", "nmc-drainage-culvert-01", 0.70, 0.90, gateway="water-gw")
        # Log occurring at minute 1 but ingested at minute 5
        add(5, "road_flooding", "police-patrol-delayed", 0.88, 0.92, payload={"original_event_minute": 1}, flags=["delayed_arrival"])
        add(6, "ambulance_delay", "108-ems-dispatch", 0.80, 0.94)

    elif name == "out_of_order_stream":
        # Out-of-order packets and network replays
        add(0, "rainfall", "weather-station-nagpur", 0.55, 0.96)
        add(2, "traffic_speed", "itms-traffic-01", 0.70, 0.90, gateway="traffic-gw")
        # Minute 1 report arriving at minute 3
        add(3, "water_level", "nmc-drainage-culvert-01", 0.65, 0.88, gateway="water-gw", flags=["delayed_arrival"])
        # Duplicate of minute 2 traffic arriving at minute 4
        add(4, "traffic_speed", "itms-traffic-01", 0.70, 0.90, gateway="traffic-gw", flags=["replayed_packet"])

    elif name == "event_retractions":
        # An initial severe alarm is officially retracted after physical verification
        add(0, "rainfall", "weather-station-nagpur", 0.50, 0.96)
        add(2, "citizen_report", "social-media-claim", 0.92, 0.40, payload={"text": "Ambazari dam overflow"}, flags=["unverified"])
        add(4, "traffic_speed", "itms-traffic-01", 0.40, 0.90)
        # Official retraction at minute 5
        add(5, "retraction", "nagpur-collector-office", 0.10, 0.99, payload={"retracted_event_id": f"{name}-{seed}-1", "reason": "False alarm; sluice gates operating normally"}, flags=["official_retraction"])

    elif name in ("coordinated_rumors", "misleading"):
        # Wave of unverified bot/citizen accounts repeating identical false claims
        add(0, "rainfall", "weather-station-nagpur", 0.35, 0.96, payload={"rain_mm_h": 12.0})
        for i in range(1, 7):
            add(i, "citizen_report", f"anonymous-feed-{i}", 0.90, 0.20, payload={"misleading": True, "claim": "City-wide power grid collapse"}, flags=["unverified", "coordinated", "misleading"])
        add(7, "traffic_speed", "itms-traffic-01", 0.25, 0.90, gateway="traffic-gw", payload={"flow": "normal"})

    elif name == "contradictory_reports":
        # Citizen social feeds claim severe road inundation while official municipal camera shows clear streets
        add(0, "rainfall", "weather-station-nagpur", 0.45, 0.96)
        add(2, "citizen_report", "civic-unverified-app", 0.90, 0.35, payload={"claim": "Narendra Nagar underpass 4 feet underwater"}, flags=["unverified"])
        add(3, "road_flooding", "itms-cctv-verified", 0.15, 0.98, payload={"water_depth_cm": 2, "verified_clear": True}, flags=["ground_verified", "contradicts_rumor"])
        add(5, "traffic_speed", "itms-traffic-01", 0.25, 0.92)

    elif name == "simultaneous_unrelated":
        # A warehouse fire coincides with a routine rain shower in different zones
        add(0, "rainfall", "weather-station-nagpur", 0.40, 0.96, zone="zone-1-laxmi-nagar")
        add(2, "wildfire", "firms-thermal-modis", 0.85, 0.90, zone="zone-8-lakadganj", payload={"location": "Industrial Warehouse", "unrelated_to_weather": True})
        add(4, "traffic_speed", "itms-traffic-01", 0.65, 0.88, zone="zone-8-lakadganj", payload={"fire_truck_access": True})
        add(6, "water_level", "nmc-drainage-culvert-01", 0.30, 0.90, zone="zone-1-laxmi-nagar")

    elif name == "emergency_with_outage":
        # A genuine crisis occurs WHILE a key sensor gateway suffers a power outage
        add(0, "rainfall", "weather-station-nagpur", 0.80, 0.96, payload={"rain_mm_h": 68.0})
        add(1, "water_level", "nmc-drainage-culvert-01", 0.85, 0.90, gateway="water-gw")
        add(2, "gateway_failure", "traffic-gw-south", 0.95, 0.95, gateway="traffic-gw")
        # Despite traffic gateway failing, physical flood & hospital surge confirm disaster
        add(4, "road_flooding", "traffic-police-eoc", 0.95, 0.96, flags=["ground_verified"])
        add(6, "hospital_demand", "gmch-emergency-triage", 0.85, 0.94)

    elif name == "seasonal_base_rate_drift":
        # Gradual onset of heavy monsoon baseline where frequent rain is normal
        for m in range(0, 8, 2):
            add(m, "rainfall", "weather-station-nagpur", 0.55, 0.96, payload={"rain_mm_h": 30.0, "seasonal_monsoon": True})
            add(m + 1, "traffic_speed", "itms-traffic-01", 0.35, 0.90)

    elif name == "rapid_escalation":
        # Instant extreme cloudburst (85 mm/h) triggering immediate emergency bypass
        add(0, "rainfall", "weather-station-nagpur", 0.98, 0.98, payload={"rain_mm_h": 88.0, "cloudburst": True}, flags=["emergency_cloudburst"])
        add(1, "road_flooding", "traffic-police-eoc", 0.96, 0.98, flags=["ground_verified"])
        add(2, "water_level", "nmc-drainage-culvert-01", 0.95, 0.95, gateway="water-gw")

    else:
        raise ValueError(f"Unknown scenario: {name}")

    events = []
    for i, (minute, typ, source, severity, reliability, zone, gateway, payload, flags, eid) in enumerate(specs):
        events.append(Event(
            event_id=eid,
            event_type=typ,
            source_id=source,
            event_timestamp=base_time + timedelta(minutes=minute),
            ingestion_timestamp=base_time + timedelta(minutes=minute),
            zone_id=zone,
            latitude=21.1180,
            longitude=79.1020,
            region=f"Nagpur, {zone}",
            severity=severity,
            reliability=reliability,
            gateway_id=gateway,
            payload=payload,
            quality_flags=flags,
            data_provenance="SYNTHETIC",
            geographic_precision="exact_sensor",
            admin_level="zone",
        ))
    return events
