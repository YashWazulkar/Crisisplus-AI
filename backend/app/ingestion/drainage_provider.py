"""Nagpur Municipal Corporation (NMC) Stormwater Drainage and Waterlogging Provider.

Monitors chronic waterlogging hotspots, drainage surcharge risks, and municipal pumping
stations across Nagpur's major hydrological basins (Nag, Pili, and Pora Rivers).
"""

from __future__ import annotations
import os
import time
from datetime import datetime, timezone
from typing import Any
import httpx
from .base import BaseAdapter
from ..normalization.schema import NormalizedEvent
from ..geography.nagpur_registry import (
    NAGPUR_WATERLOGGING_HOTSPOTS,
    NMC_ZONES,
)


class NagpurDrainageWaterloggingProvider(BaseAdapter):
    """Provides real-time interface for NMC flood control, IoT level sensors, and pumping telemetry."""

    def __init__(
        self,
        name: str = "nmc-drainage-waterlogging",
        polling_interval_seconds: int = 120,
    ):
        super().__init__(name=name, source_type="municipal_drainage_iot", polling_interval_seconds=polling_interval_seconds)
        self.iot_endpoint = os.getenv("NMC_DRAINAGE_IOT_URL", "").strip()
        self.api_key = os.getenv("NMC_DRAINAGE_API_KEY", "").strip()
        self.hotspots = NAGPUR_WATERLOGGING_HOTSPOTS

        if not self.iot_endpoint:
            self.status = "awaiting_sensor_deployment"
            self.last_error = (
                "NMC_DRAINAGE_IOT_URL not configured. "
                "Interface active in municipal baseline monitoring mode. "
                "Ultrasonic water-level sensor telemetry awaiting municipal ICCC sensor stream."
            )

    async def fetch_events(self, current_rainfall_mm_h: float = 0.0) -> list[NormalizedEvent]:
        start_time = time.perf_counter()
        self.iot_endpoint = os.getenv("NMC_DRAINAGE_IOT_URL", "").strip()

        # If live NMC IoT sensor gateway is configured:
        if self.iot_endpoint:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
                    resp = await client.get(self.iot_endpoint, headers=headers)
                    if resp.status_code == 200:
                        events = self._parse_live_iot(resp.json())
                        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                        self.record_success(len(events), elapsed_ms)
                        return events
                    else:
                        self.record_failure(f"HTTP {resp.status_code} from NMC Drainage endpoint")
            except Exception as e:
                self.record_failure(e)

        # In baseline / pre-sensor deployment mode:
        # Evaluate documented hydrological vulnerability against observed rainfall
        events = self._evaluate_hydrological_vulnerability(current_rainfall_mm_h)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        self.last_fetch_time = datetime.now(timezone.utc)
        self.latency_ms = round(elapsed_ms, 1)
        return events

    def _parse_live_iot(self, data: list[dict[str, Any]] | dict[str, Any]) -> list[NormalizedEvent]:
        """Parses verified telemetry from NMC ultrasonic water-level sensors."""
        events: list[NormalizedEvent] = []
        now_utc = datetime.now(timezone.utc)
        records = data if isinstance(data, list) else data.get("sensors", [])

        for r in records:
            hotspot_id = r.get("hotspot_id", "unknown-hotspot")
            water_depth_cm = float(r.get("water_depth_cm", 0.0))
            lat = float(r.get("latitude", 21.1458))
            lon = float(r.get("longitude", 79.0882))
            zone_id = r.get("zone_id", "zone-4-dhantoli")
            zone_meta = NMC_ZONES.get(zone_id, {})

            # Severity: 0cm=0.10, 15cm=0.45, 30cm=0.75, 60cm+=0.95
            severity = min(0.98, max(0.10, 0.10 + (water_depth_cm / 60.0) * 0.85))
            is_flooded = water_depth_cm >= 15.0

            events.append(
                NormalizedEvent(
                    source_id=self.name,
                    external_id=f"nmc-wl-{hotspot_id}-{int(now_utc.timestamp())}",
                    event_type="water_level" if not is_flooded else "road_flooding",
                    title=f"Water Level Telemetry: {water_depth_cm:.1f} cm ({r.get('location_name', hotspot_id)})",
                    description=(
                        f"NMC Ultrasonic Sensor indicates water depth of {water_depth_cm:.1f} cm "
                        f"in {zone_meta.get('name', zone_id)}. Pumping station status: {r.get('pumps_active', 1)} active."
                    ),
                    latitude=lat,
                    longitude=lon,
                    region=f"Nagpur, {zone_meta.get('name', 'NMC')}",
                    zone_id=zone_meta.get("name", zone_id),
                    assigned_zone_id=zone_id,
                    assigned_zone_name=zone_meta.get("name", zone_id),
                    geographic_precision="exact_sensor",
                    admin_level="hotspot",
                    is_nagpur_relevant=True,
                    event_timestamp=now_utc,
                    ingestion_timestamp=now_utc,
                    data_provenance="LIVE",
                    severity=round(severity, 3),
                    magnitude=water_depth_cm,
                    magnitude_unit="cm (water depth)",
                    source_reliability=0.94,
                    confidence=0.92,
                    verification_status="official",
                    source_url="https://www.nmcnagpur.gov.in/",
                    quality_flags=["iot_ultrasonic_sensor", "calibrated_telemetry"],
                    payload=r,
                )
            )
        return events

    def _evaluate_hydrological_vulnerability(self, rain_rate: float) -> list[NormalizedEvent]:
        """Generates transparent, evidence-grounded risk indicators based on observed rainfall
        and documented municipal runoff capacity for chronic hotspots.
        """
        now_utc = datetime.now(timezone.utc)
        events: list[NormalizedEvent] = []

        # If rain exceeds threshold for chronic low-clearance underpasses
        for h in self.hotspots:
            thresh = h["submersion_threshold_mm_h"]
            zone_meta = NMC_ZONES.get(h["zone_id"], {})

            if rain_rate >= thresh:
                # Rainfall exceeds design drain capacity
                ratio = rain_rate / thresh
                severity = min(0.96, max(0.55, 0.50 + (ratio - 1.0) * 0.35))
                events.append(
                    NormalizedEvent(
                        source_id=self.name,
                        external_id=f"nmc-vuln-{h['id']}-{now_utc.strftime('%Y%m%d%H%M')}",
                        event_type="drainage_overflow",
                        title=f"Drainage Capacity Exceeded: {h['name']}",
                        description=(
                            f"Current rainfall ({rain_rate:.1f} mm/h) exceeds documented municipal stormwater "
                            f"capacity ({thresh:.1f} mm/h) for {h['name']} ({zone_meta.get('name')}). "
                            f"{h['impact_description']}"
                        ),
                        latitude=h["latitude"],
                        longitude=h["longitude"],
                        region="Nagpur Municipal Corporation",
                        zone_id=zone_meta.get("name", h["zone_id"]),
                        assigned_zone_id=h["zone_id"],
                        assigned_zone_name=zone_meta.get("name", h["zone_id"]),
                        geographic_precision="hotspot_level",
                        admin_level="hotspot",
                        is_nagpur_relevant=True,
                        event_timestamp=now_utc,
                        ingestion_timestamp=now_utc,
                        data_provenance="LIVE" if rain_rate > 0 else "CACHED",
                        severity=round(severity, 3),
                        magnitude=rain_rate,
                        magnitude_unit="mm/h rainfall vs drain threshold",
                        source_reliability=0.88,
                        confidence=0.82,
                        verification_status="preliminary",
                        source_url="https://www.nmcnagpur.gov.in/",
                        quality_flags=["chronic_waterlogging_hotspot", "drainage_model_surcharge"],
                        payload={
                            "hotspot_id": h["id"],
                            "drainage_basin": h["drainage_basin"],
                            "threshold_mm_h": thresh,
                            "observed_rainfall_mm_h": rain_rate,
                            "impact": h["impact_description"],
                            "drainage_status": "Design storm threshold exceeded",
                        },
                    )
                )

        return events
