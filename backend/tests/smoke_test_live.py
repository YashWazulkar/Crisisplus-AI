"""Standalone Live Connectivity Smoke Test.

Run this script directly to verify real-time network connectivity to external feeds:
  python backend/tests/smoke_test_live.py
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.open_meteo import OpenMeteoAdapter
from app.ingestion.usgs_earthquake import USGSEarthquakeAdapter
from app.ingestion.gdacs import GDACSAdapter
from app.ingestion.nasa_firms import NASAFIRMSAdapter

async def main():
    print("=" * 65)
    print("CrisisPulse AI - Live Ingestion Connectivity Smoke Test")
    print("=" * 65)

    # 1. Open-Meteo
    print("\n[1/4] Probing Open-Meteo Weather API (Mumbai, India)...")
    weather = OpenMeteoAdapter(latitude=19.076, longitude=72.877, location_name="Mumbai, India")
    w_events = await weather.fetch_events()
    print(f"  Status: {weather.status.upper()} (Latency: {weather.latency_ms:.1f}ms)")
    print(f"  Events retrieved: {len(w_events)}")
    if w_events:
        print(f"  Sample: {w_events[0].title} | Severity: {w_events[0].severity:.2f}")

    # 2. USGS Earthquakes
    print("\n[2/4] Probing USGS Global Seismic Feed...")
    seismic = USGSEarthquakeAdapter(min_magnitude=2.0)
    s_events = await seismic.fetch_events()
    print(f"  Status: {seismic.status.upper()} (Latency: {seismic.latency_ms:.1f}ms)")
    print(f"  Events retrieved: {len(s_events)}")
    if s_events:
        print(f"  Sample: {s_events[0].title} | Depth: {s_events[0].depth_km}km")

    # 3. GDACS
    print("\n[3/4] Probing GDACS Global Disaster Alert Feed...")
    gdacs = GDACSAdapter()
    g_events = await gdacs.fetch_events()
    print(f"  Status: {gdacs.status.upper()} (Latency: {gdacs.latency_ms:.1f}ms)")
    print(f"  Events retrieved: {len(g_events)}")
    if g_events:
        print(f"  Sample: {g_events[0].title} | Region: {g_events[0].region}")

    # 4. NASA FIRMS
    print("\n[4/4] Probing NASA FIRMS Satellite Fire Detection...")
    fire = NASAFIRMSAdapter()
    f_events = await fire.fetch_events()
    print(f"  Status: {fire.status.upper()}")
    print(f"  Events retrieved: {len(f_events)}")
    if f_events:
        print(f"  Sample: {f_events[0].title} | FRP: {f_events[0].magnitude} MW")

    print("\n" + "=" * 65)
    print("Smoke test completed.")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
