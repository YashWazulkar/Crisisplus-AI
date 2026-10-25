"""Integration Tests for FastAPI Endpoints, Geography, and xAI."""

import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

def test_api_status_and_state():
    async def _test():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/")
            assert resp.status_code == 200
            data = resp.json()
            assert "CrisisPulse AI" in data["name"]
            assert "Nagpur" in data["monitoring_region"]

            state_resp = await client.get("/api/state")
            assert state_resp.status_code == 200
            state = state_resp.json()
            assert "hypotheses" in state
            assert "probabilities" in state
            assert "sources_health" in state
            assert "monitored_location" in state
            assert "Nagpur" in state["monitored_location"]["name"]
            assert "risk_overview" in state
            assert "xai_explanation" in state
            assert "subregions" in state
            assert len(state["subregions"]) == 10

    asyncio.run(_test())

def test_geography_endpoints():
    async def _test():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            geo_resp = await client.get("/api/geography/master")
            assert geo_resp.status_code == 200
            geo = geo_resp.json()
            assert "district_boundary" in geo
            assert "zones" in geo
            assert "hotspots" in geo
            assert "hospitals" in geo
            assert "hydrology" in geo

            zones_resp = await client.get("/api/geography/zones")
            assert zones_resp.status_code == 200
            assert len(zones_resp.json()["features"]) == 10

            hotspots_resp = await client.get("/api/geography/hotspots")
            assert hotspots_resp.status_code == 200
            assert len(hotspots_resp.json()["features"]) >= 7

            region_resp = await client.get("/api/region/zone-3-hanuman-nagar")
            assert region_resp.status_code == 200
            reg = region_resp.json()
            assert reg["name"] == "Hanuman Nagar Zone"
            assert "xai_explanation" in reg

    asyncio.run(_test())

def test_xai_explain_endpoint():
    async def _test():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/xai/explain", json={"zone_id": "zone-2-dharampeth"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["zone_id"] == "zone-2-dharampeth"
            assert "xai_explanation" in data
            assert data["xai_explanation"]["grounding_verified"] is True

    asyncio.run(_test())

def test_mode_switching():
    async def _test():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/mode", json={"mode": "simulation"})
            assert resp.status_code == 200
            assert resp.json()["mode"] == "simulation"

            resp_live = await client.post("/api/mode", json={"mode": "live"})
            assert resp_live.status_code == 200
            assert resp_live.json()["mode"] == "live"

    asyncio.run(_test())

def test_lab_endpoints():
    async def _test():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            replay_resp = await client.get("/api/lab/replay?scenario=cascade")
            assert replay_resp.status_code == 200
            assert len(replay_resp.json()["timeline"]) == 11

            twin_resp = await client.get("/api/lab/twin-test")
            assert twin_resp.status_code == 200
            assert "divergence_minute" in twin_resp.json()

            cf_resp = await client.post("/api/lab/counterfactual", json={"counterfactual_type": "independent_confirmation"})
            assert cf_resp.status_code == 200
            assert cf_resp.json()["is_hypothetical"] is True

    asyncio.run(_test())

def test_evaluation_and_export():
    async def _test():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            eval_resp = await client.get("/api/evaluation/latest")
            assert eval_resp.status_code == 200
            assert "metrics" in eval_resp.json()

            export_resp = await client.get("/api/export")
            assert export_resp.status_code == 200
            export_data = export_resp.json()
            assert "snapshot" in export_data
            assert "audit_ledger" in export_data

    asyncio.run(_test())
