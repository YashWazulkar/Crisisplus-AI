"""Open-Meteo Weather Ingestion Adapter for Nagpur.

Retrieves meteorological telemetry and short-range projections for Nagpur
(Centroid: 21.1458° N, 79.0882° E, Elevation: ~310m MSL).
Enforces explicit separation between direct current observations and model forecasts.
"""

from __future__ import annotations
import time
from datetime import datetime, timezone
import httpx
from .base import BaseAdapter
from ..normalization.schema import NormalizedEvent
from ..geography.nagpur_registry import (
    NAGPUR_CENTER_LAT,
    NAGPUR_CENTER_LON,
    NAGPUR_DISTRICT_NAME,
    NAGPUR_STATE,
)
from ..geography.spatial_filter import NagpurSpatialFilter

# WMO Weather interpretation codes
WMO_DESCRIPTIONS = {
    0: ("Clear sky", 0.0),
    1: ("Mainly clear", 0.05),
    2: ("Partly cloudy", 0.1),
    3: ("Overcast", 0.2),
    45: ("Fog", 0.3),
    48: ("Depositing rime fog", 0.35),
    51: ("Light drizzle", 0.25),
    53: ("Moderate drizzle", 0.35),
    55: ("Dense drizzle", 0.45),
    61: ("Slight rain", 0.35),
    63: ("Moderate rain", 0.55),
    65: ("Heavy rain", 0.80),
    71: ("Slight snow fall", 0.40),
    73: ("Moderate snow fall", 0.60),
    75: ("Heavy snow fall", 0.85),
    80: ("Slight rain showers", 0.40),
    81: ("Moderate rain showers", 0.60),
    82: ("Violent rain showers", 0.90),
    95: ("Thunderstorm", 0.75),
    96: ("Thunderstorm with slight hail", 0.85),
    99: ("Thunderstorm with heavy hail", 0.95),
}


class OpenMeteoAdapter(BaseAdapter):
    """Fetches meteorological observations and model forecasts for Nagpur from Open-Meteo."""

    def __init__(
        self,
        name: str = "open-meteo-nagpur",
        latitude: float = NAGPUR_CENTER_LAT,
        longitude: float = NAGPUR_CENTER_LON,
        location_name: str = f"{NAGPUR_DISTRICT_NAME}, {NAGPUR_STATE}, India",
        polling_interval_seconds: int = 60,
    ):
        super().__init__(name=name, source_type="weather_api", polling_interval_seconds=polling_interval_seconds)
        self.latitude = latitude
        self.longitude = longitude
        self.location_name = location_name
        self.spatial_filter = NagpurSpatialFilter()

    def set_location(self, lat: float, lon: float, name: str | None = None):
        self.latitude = lat
        self.longitude = lon
        if name:
            self.location_name = name

    async def fetch_events(self, client: httpx.AsyncClient | None = None) -> list[NormalizedEvent]:
        if client is not None:
            return await self._fetch(client)
        async with httpx.AsyncClient(timeout=10.0) as cl:
            return await self._fetch(cl)

    async def _fetch(self, client: httpx.AsyncClient) -> list[NormalizedEvent]:
        start_time = time.perf_counter()
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={self.latitude}&longitude={self.longitude}"
            f"&current=temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,surface_pressure,wind_speed_10m,wind_gusts_10m"
            f"&hourly=precipitation_probability,precipitation"
            f"&timezone=auto"
        )

        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                self.record_failure(f"HTTP {resp.status_code}: {resp.text[:120]}")
                return []
            data = resp.json()

            current = data.get("current", {})
            if not current:
                self.record_failure("Empty 'current' payload from Open-Meteo")
                return []

            obs_time_raw = current.get("time")
            try:
                obs_time = datetime.fromisoformat(obs_time_raw).replace(tzinfo=timezone.utc)
            except Exception:
                obs_time = datetime.now(timezone.utc)

            temp = float(current.get("temperature_2m", 0.0))
            precip = float(current.get("precipitation", 0.0))
            rain = float(current.get("rain", 0.0))
            wind_speed = float(current.get("wind_speed_10m", 0.0))
            wind_gusts = float(current.get("wind_gusts_10m", 0.0))
            weather_code = int(current.get("weather_code", 0))
            pressure = float(current.get("surface_pressure", 1013.25))
            humidity = float(current.get("relative_humidity_2m", 50))

            wmo_desc, wmo_base_severity = WMO_DESCRIPTIONS.get(weather_code, ("Variable conditions", 0.2))
            events: list[NormalizedEvent] = []

            # Spatial classification using Nagpur filter
            spatial_meta = self.spatial_filter.classify_event(
                self.latitude,
                self.longitude,
                region_str=self.location_name,
                source_is_district_level=True,
            )

            # 1. Direct Rainfall observation
            if precip > 0.0 or rain > 0.0:
                rain_val = max(precip, rain)
                # Precipitation intensity mapping
                rain_severity = min(0.98, max(0.25, 0.25 + (rain_val / 60.0) * 0.70))
                events.append(
                    NormalizedEvent(
                        source_id=self.name,
                        external_id=f"om-rain-{self.latitude:.4f}-{self.longitude:.4f}-{obs_time_raw}",
                        event_type="rainfall",
                        title=f"Precipitation: {rain_val:.1f} mm/h ({self.location_name})",
                        description=(
                            f"Open-Meteo weather station indicates {wmo_desc.lower()} with "
                            f"{rain_val:.1f} mm/h precipitation over Nagpur district. "
                            f"Temperature {temp}°C, humidity {humidity}%, pressure {pressure:.1f} hPa."
                        ),
                        latitude=self.latitude,
                        longitude=self.longitude,
                        region=self.location_name,
                        zone_id=spatial_meta.assigned_zone_name or "Nagpur District",
                        assigned_zone_id=spatial_meta.assigned_zone_id,
                        assigned_zone_name=spatial_meta.assigned_zone_name,
                        geographic_precision="district_level",
                        admin_level="district",
                        is_nagpur_relevant=True,
                        event_timestamp=obs_time,
                        severity=round(rain_severity, 3),
                        magnitude=round(rain_val, 2),
                        magnitude_unit="mm/h",
                        source_reliability=0.92,
                        confidence=0.88,
                        verification_status="official",
                        data_provenance="LIVE",
                        source_url="https://open-meteo.com/",
                        quality_flags=[] if rain_val < 35.0 else ["severe_rainfall_anomaly"],
                        payload={
                            "temperature_c": temp,
                            "relative_humidity_pct": humidity,
                            "precipitation_mm": precip,
                            "pressure_hpa": pressure,
                            "wind_speed_kmh": wind_speed,
                            "wmo_code": weather_code,
                            "wmo_text": wmo_desc,
                            "spatial_classification": "district_level",
                        },
                    )
                )

            # 2. Wind Gust observation
            if wind_gusts >= 35.0 or wind_speed >= 30.0:
                gust_severity = min(0.98, max(0.3, 0.2 + (wind_gusts / 120.0) * 0.75))
                events.append(
                    NormalizedEvent(
                        source_id=self.name,
                        external_id=f"om-wind-{self.latitude:.4f}-{self.longitude:.4f}-{obs_time_raw}",
                        event_type="wind_gust",
                        title=f"Elevated Wind Gusts: {wind_gusts:.1f} km/h ({self.location_name})",
                        description=f"Elevated wind velocity in Nagpur: sustained {wind_speed:.1f} km/h with peak gusts reaching {wind_gusts:.1f} km/h.",
                        latitude=self.latitude,
                        longitude=self.longitude,
                        region=self.location_name,
                        zone_id=spatial_meta.assigned_zone_name or "Nagpur District",
                        assigned_zone_id=spatial_meta.assigned_zone_id,
                        assigned_zone_name=spatial_meta.assigned_zone_name,
                        geographic_precision="district_level",
                        admin_level="district",
                        is_nagpur_relevant=True,
                        event_timestamp=obs_time,
                        severity=round(gust_severity, 3),
                        magnitude=round(wind_gusts, 1),
                        magnitude_unit="km/h",
                        source_reliability=0.92,
                        confidence=0.85,
                        verification_status="official",
                        data_provenance="LIVE",
                        source_url="https://open-meteo.com/",
                        quality_flags=[] if wind_gusts < 70.0 else ["gale_force_gusts"],
                        payload={"wind_speed_kmh": wind_speed, "wind_gusts_kmh": wind_gusts, "wmo_code": weather_code},
                    )
                )

            # 3. Severe Weather alert if WMO code indicates thunderstorm/hail
            if weather_code in (95, 96, 99) or (weather_code == 82 and not events):
                events.append(
                    NormalizedEvent(
                        source_id=self.name,
                        external_id=f"om-severe-{self.latitude:.4f}-{self.longitude:.4f}-{obs_time_raw}",
                        event_type="severe_weather",
                        title=f"Severe Storm Warning: {wmo_desc} (Nagpur)",
                        description=f"WMO classification indicates active {wmo_desc} over Nagpur. Temperature {temp}°C, pressure {pressure:.1f} hPa.",
                        latitude=self.latitude,
                        longitude=self.longitude,
                        region=self.location_name,
                        zone_id=spatial_meta.assigned_zone_name or "Nagpur District",
                        assigned_zone_id=spatial_meta.assigned_zone_id,
                        assigned_zone_name=spatial_meta.assigned_zone_name,
                        geographic_precision="district_level",
                        admin_level="district",
                        is_nagpur_relevant=True,
                        event_timestamp=obs_time,
                        severity=wmo_base_severity,
                        magnitude=float(weather_code),
                        magnitude_unit="WMO Code",
                        source_reliability=0.94,
                        confidence=0.90,
                        verification_status="official",
                        data_provenance="LIVE",
                        source_url="https://open-meteo.com/",
                        quality_flags=["thunderstorm_alert"],
                        payload={"wmo_code": weather_code, "wmo_text": wmo_desc, "temperature_c": temp},
                    )
                )

            # 4. Supplemental Near-Term Forecast Event (explicitly labeled FORECAST)
            hourly = data.get("hourly", {})
            hourly_times = hourly.get("time", [])
            hourly_prob = hourly.get("precipitation_probability", [])
            hourly_precip = hourly.get("precipitation", [])
            if len(hourly_times) > 1 and len(hourly_precip) > 1:
                next_hr_precip = float(hourly_precip[1] or 0.0)
                next_hr_prob = float(hourly_prob[1] or 0.0) / 100.0 if hourly_prob else 0.0
                if next_hr_precip >= 5.0 or next_hr_prob >= 0.50:
                    events.append(
                        NormalizedEvent(
                            source_id=self.name,
                            external_id=f"om-forecast-1h-{self.latitude:.4f}-{self.longitude:.4f}-{hourly_times[1]}",
                            event_type="rainfall",
                            title=f"Weather Outlook (+1h): {next_hr_precip:.1f} mm expected ({int(next_hr_prob*100)}% prob)",
                            description=(
                                f"Numerical model projection indicates {next_hr_precip:.1f} mm precipitation "
                                f"probability {int(next_hr_prob*100)}% for Nagpur over the next hour. "
                                "This is a model forecast, not a verified ground observation."
                            ),
                            latitude=self.latitude,
                            longitude=self.longitude,
                            region=self.location_name,
                            zone_id="Nagpur District Forecast Scope",
                            assigned_zone_id=None,
                            assigned_zone_name="Nagpur District Outlook",
                            geographic_precision="district_level",
                            admin_level="district",
                            is_nagpur_relevant=True,
                            event_timestamp=obs_time,
                            severity=min(0.85, max(0.20, next_hr_precip / 40.0)),
                            magnitude=next_hr_precip,
                            magnitude_unit="mm (forecast)",
                            source_reliability=0.82,
                            confidence=round(next_hr_prob, 2),
                            verification_status="preliminary",
                            data_provenance="FORECAST",
                            source_url="https://open-meteo.com/",
                            quality_flags=["model_forecast", "supplemental_projection"],
                            payload={
                                "forecast_horizon": "+1 hour",
                                "precipitation_probability_pct": int(next_hr_prob * 100),
                                "expected_precipitation_mm": next_hr_precip,
                            },
                        )
                    )

            # If conditions are nominal, record a routine observation baseline
            if not events:
                events.append(
                    NormalizedEvent(
                        source_id=self.name,
                        external_id=f"om-routine-{self.latitude:.4f}-{self.longitude:.4f}-{obs_time_raw}",
                        event_type="rainfall",
                        title=f"Nagpur Weather Observation: {wmo_desc} ({temp}°C)",
                        description=(
                            f"{wmo_desc} over Nagpur. Temperature {temp}°C, humidity {humidity}%, "
                            f"wind: {wind_speed:.1f} km/h, pressure {pressure:.1f} hPa. No active precipitation."
                        ),
                        latitude=self.latitude,
                        longitude=self.longitude,
                        region=self.location_name,
                        zone_id="Nagpur Operational Region",
                        assigned_zone_id=None,
                        assigned_zone_name="Nagpur District Baseline",
                        geographic_precision="district_level",
                        admin_level="district",
                        is_nagpur_relevant=True,
                        event_timestamp=obs_time,
                        severity=max(0.05, round(wmo_base_severity * 0.4, 2)),
                        magnitude=0.0,
                        magnitude_unit="mm/h",
                        source_reliability=0.92,
                        confidence=0.95,
                        verification_status="official",
                        data_provenance="LIVE",
                        source_url="https://open-meteo.com/",
                        payload={"temperature_c": temp, "humidity_pct": humidity, "wind_speed_kmh": wind_speed, "wmo_code": weather_code},
                    )
                )

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.record_success(len(events), elapsed_ms)
            return events

        except Exception as e:
            self.record_failure(e)
            return []
