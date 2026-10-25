"""USGS Earthquake Hazards Program Ingestion Adapter for Nagpur.

Ingests official seismic feeds from the USGS Earthquake Hazards API,
passing each event through the Nagpur Spatial Filter to ensure only local or
regionally impactful seismic events enter the Nagpur operational assessment.
"""

from __future__ import annotations
import time
from datetime import datetime, timezone
import httpx
from .base import BaseAdapter
from ..normalization.schema import NormalizedEvent
from ..geography.spatial_filter import NagpurSpatialFilter


class USGSEarthquakeAdapter(BaseAdapter):
    """Retrieves real-time seismic feeds, applying spatial relevance filters for Nagpur."""

    HOURLY_FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
    DAILY_FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

    def __init__(
        self,
        name: str = "usgs-earthquake",
        min_magnitude: float = 2.0,
        polling_interval_seconds: int = 60,
        feed_mode: str = "hourly_with_daily_fallback",
        enforce_nagpur_filtering: bool = True,
    ):
        super().__init__(name=name, source_type="seismic_api", polling_interval_seconds=polling_interval_seconds)
        self.min_magnitude = min_magnitude
        self.feed_mode = feed_mode
        self.enforce_nagpur_filtering = enforce_nagpur_filtering
        self.spatial_filter = NagpurSpatialFilter()
        self.diagnostic_excluded_count = 0

    async def fetch_events(self, client: httpx.AsyncClient | None = None) -> list[NormalizedEvent]:
        if client is not None:
            return await self._fetch(client)
        async with httpx.AsyncClient(timeout=12.0) as cl:
            return await self._fetch(cl)

    async def _fetch(self, client: httpx.AsyncClient) -> list[NormalizedEvent]:
        start_time = time.perf_counter()
        feed_url = self.HOURLY_FEED

        try:
            resp = await client.get(feed_url)
            if resp.status_code != 200:
                self.record_failure(f"HTTP {resp.status_code} from USGS: {resp.text[:120]}")
                return []
            data = resp.json()

            features = data.get("features", [])

            # Fall back to daily if hourly is empty
            if not features and self.feed_mode == "hourly_with_daily_fallback":
                daily_resp = await client.get(self.DAILY_FEED)
                if daily_resp.status_code == 200:
                    daily_data = daily_resp.json()
                    features = daily_data.get("features", [])[:50]

            events: list[NormalizedEvent] = []
            for feat in features:
                props = feat.get("properties", {})
                geom = feat.get("geometry", {})
                coords = geom.get("coordinates", [0.0, 0.0, 0.0])

                lon = float(coords[0])
                lat = float(coords[1])
                depth = float(coords[2]) if len(coords) > 2 else 10.0

                mag = props.get("mag")
                if mag is None:
                    continue
                mag = float(mag)
                if mag < self.min_magnitude:
                    continue

                # Enforce spatial filtering for Nagpur
                spatial_meta = self.spatial_filter.classify_event(
                    lat, lon, region_str=props.get("place"), event_type="earthquake", magnitude=mag
                )

                if self.enforce_nagpur_filtering and not spatial_meta.is_relevant:
                    self.diagnostic_excluded_count += 1
                    continue

                event_id_ext = str(feat.get("id", f"usgs-{props.get('time', 0)}"))
                place = props.get("place") or "Nagpur Regional Seismic Zone"
                epoch_ms = props.get("time", 0)
                obs_time = datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc)
                url = props.get("url")
                review_status = props.get("status", "automatic")
                alert_level = props.get("alert")
                tsunami = int(props.get("tsunami", 0))

                # Compute normalized severity index
                if mag <= 2.0:
                    severity = 0.15 + (mag / 2.0) * 0.15
                elif mag <= 4.5:
                    severity = 0.30 + ((mag - 2.0) / 2.5) * 0.25
                elif mag <= 6.0:
                    severity = 0.55 + ((mag - 4.5) / 1.5) * 0.23
                elif mag <= 7.0:
                    severity = 0.78 + ((mag - 6.0) / 1.0) * 0.14
                else:
                    severity = min(0.99, 0.92 + ((mag - 7.0) / 3.0) * 0.07)

                quality_flags = []
                if tsunami:
                    quality_flags.append("tsunami_potential")
                if spatial_meta.downstream_impact_rationale:
                    quality_flags.append("downstream_seismic_impact")
                if alert_level:
                    quality_flags.append(f"usgs_alert_{alert_level}")

                events.append(
                    NormalizedEvent(
                        source_id=self.name,
                        external_id=event_id_ext,
                        event_type="earthquake",
                        title=f"M{mag:.1f} Earthquake: {place}",
                        description=(
                            f"Seismic event of magnitude {mag:.1f} recorded at depth {depth:.1f} km. "
                            f"USGS Review: {review_status}. {spatial_meta.downstream_impact_rationale or ''}"
                        ),
                        latitude=lat,
                        longitude=lon,
                        depth_km=depth,
                        region=place,
                        zone_id=spatial_meta.assigned_zone_name or "Nagpur Regional Perimeter",
                        assigned_zone_id=spatial_meta.assigned_zone_id,
                        assigned_zone_name=spatial_meta.assigned_zone_name,
                        geographic_precision=spatial_meta.precision,
                        admin_level=spatial_meta.admin_level,
                        is_nagpur_relevant=spatial_meta.is_relevant,
                        event_timestamp=obs_time,
                        ingestion_timestamp=datetime.now(timezone.utc),
                        data_provenance="LIVE",
                        severity=round(severity, 3),
                        magnitude=mag,
                        magnitude_unit="Richter (M)",
                        source_reliability=0.98,
                        confidence=0.92 if review_status == "reviewed" else 0.80,
                        verification_status="confirmed" if review_status == "reviewed" else "preliminary",
                        source_url=url,
                        quality_flags=quality_flags,
                        payload={
                            "place": place,
                            "depth_km": depth,
                            "review_status": review_status,
                            "alert_level": alert_level,
                            "distance_to_nagpur_km": round(spatial_meta.distance_to_center_km, 1),
                        },
                    )
                )

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.record_success(len(events), elapsed_ms)
            return events

        except Exception as e:
            self.record_failure(e)
            return []
