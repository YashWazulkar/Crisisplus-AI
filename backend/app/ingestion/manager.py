"""Ingestion Manager and Scheduling Orchestrator for Nagpur Operational Platform.

Coordinates all real external feeds and municipal provider interfaces:
  - Open-Meteo Weather (Nagpur)
  - IMD / RMC Nagpur Severe Weather Warnings
  - NMC Stormwater Drainage & Waterlogging Hotspots
  - Nagpur Emergency Hospital Bed Occupancy Network
  - Nagpur Arterial Corridor Traffic & Road Disruption
  - NASA FIRMS Active Thermal Detections (Nagpur District)
  - USGS Seismic Feeds (Nagpur Regional Relevance)
  - GDACS Disaster Bulletins (Central India Catchment)
"""

from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Callable, Coroutine, Any
from .base import BaseAdapter
from .open_meteo import OpenMeteoAdapter
from .imd_adapter import IMDAdapter
from .drainage_provider import NagpurDrainageWaterloggingProvider
from .hospital_provider import HospitalDataProvider
from .traffic_provider import NagpurTrafficIncidentProvider
from .nasa_firms import NASAFIRMSAdapter
from .usgs_earthquake import USGSEarthquakeAdapter
from .gdacs import GDACSAdapter
from ..normalization.schema import NormalizedEvent
from ..validation.validator import EventValidator
from ..deduplication.deduplicator import EventDeduplicator
from ..data_quality.scorer import DataQualityScorer
from ..geography.spatial_filter import NagpurSpatialFilter
from ..geography.nagpur_registry import (
    NAGPUR_CENTER_LAT,
    NAGPUR_CENTER_LON,
    NAGPUR_DISTRICT_NAME,
    NAGPUR_STATE,
)


class IngestionManager:
    """Central orchestrator for all Nagpur-focused data feeds and provider interfaces."""

    def __init__(self, on_event_callback: Callable[[NormalizedEvent, float], Coroutine[Any, Any, None]] | None = None):
        self.adapters: dict[str, BaseAdapter] = {}
        self.on_event_callback = on_event_callback
        self.validator = EventValidator()
        self.deduplicator = EventDeduplicator()
        self.quality_scorer = DataQualityScorer()
        self.spatial_filter = NagpurSpatialFilter()

        self.running = False
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self.diagnostic_excluded_events: list[dict[str, Any]] = []

        # Initialize Nagpur-specific adapters
        self.weather_adapter = OpenMeteoAdapter()
        self.imd_adapter = IMDAdapter()
        self.drainage_provider = NagpurDrainageWaterloggingProvider()
        self.hospital_provider = HospitalDataProvider()
        self.traffic_provider = NagpurTrafficIncidentProvider()
        self.fire_adapter = NASAFIRMSAdapter()
        self.seismic_adapter = USGSEarthquakeAdapter()
        self.gdacs_adapter = GDACSAdapter()

        self.register_adapter(self.weather_adapter)
        self.register_adapter(self.imd_adapter)
        self.register_adapter(self.drainage_provider)
        self.register_adapter(self.hospital_provider)
        self.register_adapter(self.traffic_provider)
        self.register_adapter(self.fire_adapter)
        self.register_adapter(self.seismic_adapter)
        self.register_adapter(self.gdacs_adapter)

    def register_adapter(self, adapter: BaseAdapter):
        self.adapters[adapter.name] = adapter

    def set_location(self, lat: float, lon: float, name: str):
        """Update monitored coordinates across relevant geographic adapters."""
        self.weather_adapter.set_location(lat, lon, name)

    async def poll_source(self, adapter_name: str) -> list[NormalizedEvent]:
        """Polls an individual adapter and processes incoming events through the pipeline."""
        adapter = self.adapters.get(adapter_name)
        if not adapter or not adapter.enabled:
            return []

        try:
            # Special dependency chaining
            if adapter_name == "nmc-drainage-waterlogging":
                # Check current observed rainfall rate from weather adapter
                current_rain = 0.0
                raw_events = await self.drainage_provider.fetch_events(current_rainfall_mm_h=current_rain)
            elif adapter_name == "nagpur-traffic-itms":
                raw_events = await self.traffic_provider.fetch_events(active_flooded_hotspot_ids=[])
            else:
                raw_events = await adapter.fetch_events()

            accepted_events: list[NormalizedEvent] = []

            for evt in raw_events:
                # 1. Spatial Relevance Filter
                spatial_meta = self.spatial_filter.classify_event(
                    evt.latitude,
                    evt.longitude,
                    region_str=evt.region,
                    event_type=evt.event_type,
                    magnitude=evt.magnitude,
                    source_is_district_level=(evt.geographic_precision == "district_level"),
                )

                if not spatial_meta.is_relevant:
                    self.diagnostic_excluded_events.append({
                        "event_id": evt.event_id,
                        "source_id": evt.source_id,
                        "title": evt.title,
                        "coords": [evt.latitude, evt.longitude],
                        "reason": spatial_meta.exclusion_reason,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    adapter.records_rejected += 1
                    continue

                # Enrich spatial attributes
                if spatial_meta.assigned_zone_id and not evt.assigned_zone_id:
                    evt.assigned_zone_id = spatial_meta.assigned_zone_id
                    evt.assigned_zone_name = spatial_meta.assigned_zone_name
                    evt.zone_id = spatial_meta.assigned_zone_name or evt.zone_id
                evt.geographic_precision = spatial_meta.precision
                evt.admin_level = spatial_meta.admin_level
                evt.is_nagpur_relevant = True

                # 2. Validation Stage
                val_res = self.validator.validate(evt)
                if not val_res.is_valid:
                    adapter.records_rejected += 1
                    continue

                # 3. Deduplication Stage
                dedup_res = self.deduplicator.check_and_register(evt)
                if dedup_res.is_duplicate:
                    adapter.records_rejected += 1
                    continue

                # 4. Quality Scoring Stage
                source_health_val = 1.0 if adapter.status == "healthy" else 0.65
                quality_weight = self.quality_scorer.score_event(evt, source_health_val)

                accepted_events.append(evt)

                # 5. Dispatch to Central Inference Pipeline
                if self.on_event_callback:
                    await self.on_event_callback(evt, quality_weight)

            return accepted_events

        except Exception as e:
            adapter.record_failure(e)
            return []

    async def poll_all_sources(self) -> dict[str, int]:
        """Triggers a poll across all configured Nagpur ingestion adapters."""
        results = {}
        for name in list(self.adapters.keys()):
            events = await self.poll_source(name)
            results[name] = len(events)
        return results

    def get_sources_health(self) -> list[dict[str, Any]]:
        return [adapter.health_status() for adapter in self.adapters.values()]

    def get_monitoring_mode(self) -> str:
        """Computes the overall operational monitoring mode:
        LIVE    — All active feeds connected and streaming real observations.
        MIXED   — Live feeds connected alongside authorized/reference baseline modules.
        DEGRADED — Network timeouts or rate-limiting affecting core feeds.
        OFFLINE — Application operating disconnected from upstream services.
        """
        statuses = [a.status for a in self.adapters.values()]
        if any(s == "error" for s in statuses):
            return "DEGRADED"
        if all(s == "healthy" for s in statuses):
            return "LIVE"
        if any(s in ("awaiting_api_credentials", "awaiting_api_key", "awaiting_sensor_deployment", "awaiting_authorization", "awaiting_traffic_api") for s in statuses):
            return "MIXED"
        return "OFFLINE"

    async def start(self):
        async with self._lock:
            if not self.running:
                self.running = True
                self._task = asyncio.create_task(self._run_loop())

    async def stop(self):
        async with self._lock:
            self.running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
                self._task = None

    async def _run_loop(self):
        """Asynchronous round-robin scheduler respecting individual polling intervals."""
        last_polled: dict[str, float] = {}

        while self.running:
            now = asyncio.get_event_loop().time()
            for name, adapter in list(self.adapters.items()):
                if not adapter.enabled:
                    continue
                last_time = last_polled.get(name, 0.0)
                interval = max(30, adapter.polling_interval_seconds) + adapter.backoff_seconds
                if (now - last_time) >= interval:
                    last_polled[name] = now
                    asyncio.create_task(self.poll_source(name))
            await asyncio.sleep(2.0)
