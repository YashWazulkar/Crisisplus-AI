"""GDACS (Global Disaster Alert and Coordination System) Ingestion Adapter for Nagpur.

Ingests multi-hazard international disaster alerts published by GDACS (UN / European Commission),
applying spatial relevance filters to ensure only events impacting Nagpur or its upstream
hydrological / geological catchments enter the operational assessment.
"""

from __future__ import annotations
import time
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
import httpx
from .base import BaseAdapter
from ..normalization.schema import NormalizedEvent
from ..geography.spatial_filter import NagpurSpatialFilter

GDACS_HAZARD_MAP = {
    "EQ": "earthquake",
    "TC": "cyclone",
    "FL": "flood",
    "VO": "severe_weather",
    "WF": "wildfire",
    "DR": "severe_weather",
}


class GDACSAdapter(BaseAdapter):
    """Fetches disaster alerts from GDACS, filtering strictly for Nagpur regional relevance."""

    FEED_URL = "https://www.gdacs.org/xml/rss.xml"

    def __init__(
        self,
        name: str = "gdacs-global",
        polling_interval_seconds: int = 300,
        enforce_nagpur_filtering: bool = True,
    ):
        super().__init__(name=name, source_type="disaster_feed", polling_interval_seconds=polling_interval_seconds)
        self.enforce_nagpur_filtering = enforce_nagpur_filtering
        self.spatial_filter = NagpurSpatialFilter()
        self.diagnostic_excluded_count = 0

    async def fetch_events(self, client: httpx.AsyncClient | None = None) -> list[NormalizedEvent]:
        if client is not None:
            return await self._fetch(client)
        async with httpx.AsyncClient(timeout=15.0) as cl:
            return await self._fetch(cl)

    async def _fetch(self, client: httpx.AsyncClient) -> list[NormalizedEvent]:
        start_time = time.perf_counter()

        try:
            resp = await client.get(self.FEED_URL, headers={"User-Agent": "CrisisPulseAI-Nagpur/2.5"})
            if resp.status_code != 200:
                self.record_failure(f"HTTP {resp.status_code} from GDACS: {resp.text[:120]}")
                return []
            xml_text = resp.text

            root = ET.fromstring(xml_text)
            channel = root.find("channel")
            if channel is None:
                channel = root

            items = channel.findall("item")
            events: list[NormalizedEvent] = []

            ns = {
                "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
                "gdacs": "http://www.gdacs.org",
                "georss": "http://www.georss.org/georss",
            }

            for item in items[:40]:
                title_elem = item.find("title")
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else "GDACS Alert"
                desc_elem = item.find("description")
                desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""
                link_elem = item.find("link")
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else "https://www.gdacs.org"
                guid_elem = item.find("guid")
                guid = guid_elem.text.strip() if guid_elem is not None and guid_elem.text else title

                pubdate_elem = item.find("pubDate")
                if pubdate_elem is not None and pubdate_elem.text:
                    try:
                        obs_time = parsedate_to_datetime(pubdate_elem.text).astimezone(timezone.utc)
                    except Exception:
                        obs_time = datetime.now(timezone.utc)
                else:
                    obs_time = datetime.now(timezone.utc)

                lat, lon = 0.0, 0.0
                lat_elem = item.find("geo:lat", ns)
                lon_elem = item.find("geo:long", ns)
                if lat_elem is not None and lon_elem is not None and lat_elem.text and lon_elem.text:
                    try:
                        lat = float(lat_elem.text)
                        lon = float(lon_elem.text)
                    except ValueError:
                        pass
                else:
                    point_elem = item.find("georss:point", ns)
                    if point_elem is not None and point_elem.text:
                        parts = point_elem.text.strip().split()
                        if len(parts) >= 2:
                            try:
                                lat, lon = float(parts[0]), float(parts[1])
                            except ValueError:
                                pass

                event_type_raw = ""
                ev_elem = item.find("gdacs:eventtype", ns)
                if ev_elem is not None and ev_elem.text:
                    event_type_raw = ev_elem.text.strip()

                alert_level = ""
                al_elem = item.find("gdacs:alertlevel", ns)
                if al_elem is not None and al_elem.text:
                    alert_level = al_elem.text.strip()

                country = ""
                country_elem = item.find("gdacs:country", ns)
                if country_elem is not None and country_elem.text:
                    country = country_elem.text.strip()

                event_type = GDACS_HAZARD_MAP.get(event_type_raw, "severe_weather")

                # Spatial classification for Nagpur
                spatial_meta = self.spatial_filter.classify_event(
                    lat, lon, region_str=f"{country} {title} {desc}", event_type=event_type
                )

                if self.enforce_nagpur_filtering and not spatial_meta.is_relevant:
                    self.diagnostic_excluded_count += 1
                    continue

                if alert_level.lower() == "red":
                    severity = 0.95
                elif alert_level.lower() == "orange":
                    severity = 0.72
                else:
                    severity = 0.38

                flags = [f"gdacs_alert_{alert_level.lower()}"] if alert_level else []
                if spatial_meta.downstream_impact_rationale:
                    flags.append("regional_upstream_hazard")

                events.append(
                    NormalizedEvent(
                        source_id=self.name,
                        external_id=f"gdacs-{guid}",
                        event_type=event_type,  # type: ignore
                        title=title,
                        description=desc or f"GDACS {alert_level} alert for {country} ({event_type_raw})",
                        latitude=lat,
                        longitude=lon,
                        region=country or "Nagpur Regional Scope",
                        zone_id=spatial_meta.assigned_zone_name or "Nagpur District Scope",
                        assigned_zone_id=spatial_meta.assigned_zone_id,
                        assigned_zone_name=spatial_meta.assigned_zone_name,
                        geographic_precision=spatial_meta.precision,
                        admin_level=spatial_meta.admin_level,
                        is_nagpur_relevant=spatial_meta.is_relevant,
                        event_timestamp=obs_time,
                        ingestion_timestamp=datetime.now(timezone.utc),
                        data_provenance="LIVE",
                        severity=severity,
                        magnitude=None,
                        source_reliability=0.96,
                        confidence=0.90,
                        verification_status="official",
                        source_url=link,
                        quality_flags=flags,
                        payload={"alert_level": alert_level, "gdacs_type": event_type_raw, "country": country},
                    )
                )

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.record_success(len(events), elapsed_ms)
            return events

        except Exception as e:
            self.record_failure(e)
            return []
