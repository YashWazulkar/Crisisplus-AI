"""Tests for External Ingestion Adapters and Municipal Providers for Nagpur."""

import asyncio
import httpx
from app.ingestion.open_meteo import OpenMeteoAdapter
from app.ingestion.imd_adapter import IMDAdapter
from app.ingestion.drainage_provider import NagpurDrainageWaterloggingProvider
from app.ingestion.hospital_provider import HospitalDataProvider
from app.ingestion.traffic_provider import NagpurTrafficIncidentProvider
from app.ingestion.usgs_earthquake import USGSEarthquakeAdapter
from app.ingestion.gdacs import GDACSAdapter
from app.ingestion.nasa_firms import NASAFIRMSAdapter


def test_open_meteo_adapter_parsing():
    async def _test():
        adapter = OpenMeteoAdapter(latitude=21.1458, longitude=79.0882, location_name="Nagpur, Maharashtra, India")
        mock_resp = {
            "current": {
                "time": "2026-10-25T15:00",
                "interval": 900,
                "temperature_2m": 31.5,
                "relative_humidity_2m": 88,
                "precipitation": 42.0,
                "rain": 42.0,
                "weather_code": 65,  # Heavy rain
                "surface_pressure": 1008.2,
                "wind_speed_10m": 38.0,
                "wind_gusts_10m": 58.0,
            },
            "hourly": {
                "time": ["2026-10-25T15:00", "2026-10-25T16:00"],
                "precipitation_probability": [90, 85],
                "precipitation": [42.0, 35.0],
            }
        }
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(200, json=mock_resp))) as client:
            events = await adapter.fetch_events(client=client)

        assert len(events) >= 1
        rain_evt = next((e for e in events if e.event_type == "rainfall" and e.data_provenance == "LIVE"), None)
        assert rain_evt is not None
        assert rain_evt.magnitude == 42.0
        assert rain_evt.severity > 0.60
        assert "Nagpur" in rain_evt.region
        assert rain_evt.is_nagpur_relevant is True
        assert rain_evt.geographic_precision == "district_level"
        assert adapter.status == "healthy"
        assert adapter.records_accepted >= 1

    asyncio.run(_test())


def test_open_meteo_adapter_error_handling():
    async def _test():
        adapter = OpenMeteoAdapter()
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(503, text="Service Unavailable"))) as client:
            events = await adapter.fetch_events(client=client)

        assert len(events) == 0
        assert adapter.status == "error"
        assert adapter.consecutive_failures == 1
        assert "503" in adapter.last_error

    asyncio.run(_test())


def test_imd_adapter_reference_and_live_parsing():
    async def _test():
        adapter = IMDAdapter()
        # Test reference fallback when unconfigured
        events = await adapter.fetch_events()
        assert len(events) == 1
        ref_evt = events[0]
        assert ref_evt.source_id == "imd-rmc-nagpur"
        assert ref_evt.data_provenance == "CACHED"
        assert ref_evt.geographic_precision == "district_level"
        assert ref_evt.is_nagpur_relevant is True
        assert adapter.status == "awaiting_api_credentials"

        # Test live authenticated parsing mock
        adapter.api_key = "test-token"
        mock_warning = {
            "district_warning": {
                "district_code": "505",
                "colour_code": "ORANGE",
                "warning": "Very heavy rainfall and severe squall expected in Nagpur.",
                "issue_time": "2026-10-25T14:00:00Z",
                "valid_until": "2026-10-26T14:00:00Z",
            }
        }
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(200, json=mock_warning))) as client:
            live_events = await adapter.fetch_events(client=client)

        assert len(live_events) == 1
        live_evt = live_events[0]
        assert live_evt.data_provenance == "LIVE"
        assert live_evt.severity >= 0.70
        assert "Orange" in live_evt.title
        assert live_evt.is_nagpur_relevant is True

    asyncio.run(_test())


def test_drainage_provider_hotspot_threshold_evaluation():
    async def _test():
        provider = NagpurDrainageWaterloggingProvider()
        # Normal rain (10 mm/h) below threshold for Narendra Nagar (25 mm/h)
        evts_low = await provider.fetch_events(current_rainfall_mm_h=10.0)
        assert len(evts_low) == 0

        # Severe rain (35 mm/h) exceeds Narendra Nagar and Mankapur thresholds
        evts_high = await provider.fetch_events(current_rainfall_mm_h=35.0)
        assert len(evts_high) >= 1
        nn_evt = next((e for e in evts_high if "Narendra Nagar" in e.title), None)
        assert nn_evt is not None
        assert nn_evt.event_type == "drainage_overflow"
        assert nn_evt.severity >= 0.50
        assert nn_evt.assigned_zone_id == "zone-3-hanuman-nagar"

    asyncio.run(_test())


def test_hospital_provider_baseline():
    async def _test():
        provider = HospitalDataProvider()
        events = await provider.fetch_events()
        assert len(events) >= 2
        gmch = next((e for e in events if "GMCH" in e.title), None)
        assert gmch is not None
        assert gmch.data_provenance == "CACHED"
        assert "awaiting_api_authorization" in gmch.quality_flags
        assert provider.status == "awaiting_authorization"

    asyncio.run(_test())


def test_traffic_provider_corridor_disruption():
    async def _test():
        provider = NagpurTrafficIncidentProvider()
        # With flooded Narendra Nagar underpass
        events = await provider.fetch_events(active_flooded_hotspot_ids=["hotspot-narendra-nagar"])
        assert len(events) == 1
        evt = events[0]
        assert evt.event_type == "ambulance_delay"
        assert "GMCH" in evt.description
        assert evt.assigned_zone_id == "zone-3-hanuman-nagar"

    asyncio.run(_test())


def test_usgs_earthquake_filtering_for_nagpur():
    async def _test():
        # California quake -> should be excluded by Nagpur spatial filter
        adapter_filtered = USGSEarthquakeAdapter(min_magnitude=2.0, enforce_nagpur_filtering=True)
        mock_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": "us7000test",
                    "properties": {
                        "mag": 5.8,
                        "place": "35 km SW of Petrolia, CA",
                        "time": 1792944000000,
                        "updated": 1792945000000,
                        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us7000test",
                        "status": "reviewed",
                        "tsunami": 0,
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-124.5, 40.1, 12.4],
                    },
                }
            ]
        }

        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(200, json=mock_geojson))) as client:
            events = await adapter_filtered.fetch_events(client=client)

        # Excluded from Nagpur operational assessment!
        assert len(events) == 0
        assert adapter_filtered.diagnostic_excluded_count == 1

        # Regional central India quake -> should be accepted
        mock_regional = {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": "us_regional",
                    "properties": {
                        "mag": 5.2,
                        "place": "120 km N of Nagpur, Madhya Pradesh",
                        "time": 1792944000000,
                        "status": "reviewed",
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [79.15, 22.25, 10.0],  # ~120 km from Nagpur
                    },
                }
            ]
        }
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(200, json=mock_regional))) as client:
            reg_events = await adapter_filtered.fetch_events(client=client)

        assert len(reg_events) == 1
        assert reg_events[0].is_nagpur_relevant is True

    asyncio.run(_test())


def test_gdacs_adapter_parsing_and_filtering():
    async def _test():
        adapter = GDACSAdapter(enforce_nagpur_filtering=False)
        sample_xml = """<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0" xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#" xmlns:gdacs="http://www.gdacs.org">
          <channel>
            <title>GDACS Alerts</title>
            <item>
              <title>Red Flood Alert in Eastern Province</title>
              <description>Significant flood inundation affecting 150,000 residents.</description>
              <link>https://www.gdacs.org/report.aspx?eventid=123</link>
              <guid>gdacs-fl-123</guid>
              <pubDate>Sun, 25 Oct 2026 12:00:00 GMT</pubDate>
              <geo:lat>21.1458</geo:lat>
              <geo:long>79.0882</geo:long>
              <gdacs:eventtype>FL</gdacs:eventtype>
              <gdacs:alertlevel>Red</gdacs:alertlevel>
              <gdacs:country>India</gdacs:country>
            </item>
          </channel>
        </rss>
        """

        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(200, text=sample_xml))) as client:
            events = await adapter.fetch_events(client=client)

        assert len(events) == 1
        evt = events[0]
        assert evt.event_type == "flood"
        assert evt.severity >= 0.90
        assert evt.latitude == 21.1458
        assert evt.longitude == 79.0882
        assert "gdacs_alert_red" in evt.quality_flags

    asyncio.run(_test())


def test_nasa_firms_fallback_sample():
    adapter = NASAFIRMSAdapter()
    events = asyncio.run(adapter.fetch_events())
    assert len(events) >= 1
    assert events[0].event_type == "wildfire"
    assert "sample_reference_dataset" in events[0].quality_flags
    assert adapter.status == "awaiting_api_key"
    assert events[0].is_nagpur_relevant is True
