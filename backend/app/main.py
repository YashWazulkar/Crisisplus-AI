"""CrisisPulse AI FastAPI Application: Nagpur Operational Edition.

Integrates real-time external emergency feeds (IMD, Open-Meteo, NMC Drainage,
Hospital Capacity, Arterial Traffic, NASA FIRMS, USGS Seismic, GDACS),
Nagpur-specific geographic zoning (10 NMC zones, 7 chronic flood hotspots),
Bayesian inference across 4 hypotheses, expected-loss action gating,
online trust learning, base-rate adaptation, xAI (Grok) explainability,
and real-time WebSocket streaming.
"""

from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .engine import InferenceEngine
from .schemas import Event, NormalizedEvent
from .simulator import SCENARIOS, make_scenario_events
from .ingestion.manager import IngestionManager
from .intelligence_lab.lab import IntelligenceLab
from .evaluation.evaluator import ModelEvaluator
from .database.database import CrisisDatabase
from .geography import (
    get_nagpur_master_geojson,
    get_nagpur_zones_geojson,
    get_nagpur_hotspots_geojson,
    get_nagpur_hospitals_geojson,
    get_nagpur_hydrology_geojson,
    NMC_ZONES,
    NAGPUR_CENTER_LAT,
    NAGPUR_CENTER_LON,
    NAGPUR_DISTRICT_NAME,
    NAGPUR_STATE,
)

# Core singletons
engine = InferenceEngine()
lab = IntelligenceLab()
evaluator = ModelEvaluator()
db = CrisisDatabase()

clients: set[WebSocket] = set()

# Operating mode: "live" or "simulation"
operating_mode = "live"

# Simulation state
simulation_task = None
periodic_task = None
sim_running = False
sim_speed = 1.0
selected_scenario = "cascade"
sim_seed = 42
current_events = []
sim_cursor = 0


# Broadcast helper
async def broadcast(message: dict[str, Any]):
    stale = []
    for ws in list(clients):
        try:
            await ws.send_json(message)
        except Exception:
            stale.append(ws)
    for ws in stale:
        clients.discard(ws)


# Ingestion event callback
async def handle_live_event(event: NormalizedEvent, quality_weight: float):
    if operating_mode == "live":
        result = engine.process(event)
        if result.get("accepted"):
            snap = get_unified_snapshot()
            await broadcast({"type": "live_event", "result": result, "snapshot": snap})


ingestion_manager = IngestionManager(on_event_callback=handle_live_event)


# Background periodic 1-minute assessment loop
async def minute_assessment_loop():
    while True:
        try:
            await asyncio.sleep(60.0)
            if operating_mode == "live":
                tick_res = engine.tick_minute()
                snap = get_unified_snapshot()
                await broadcast({"type": "periodic_tick", "result": tick_res, "snapshot": snap})
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(5.0)


# Simulation loop (preserved for Testing/Demo Mode)
async def simulation_loop():
    global sim_running, sim_cursor
    while sim_running and sim_cursor < len(current_events):
        event = current_events[sim_cursor]
        result = engine.process(event)
        sim_cursor += 1
        if result.get("accepted"):
            snap = get_unified_snapshot()
            await broadcast({"type": "sim_update", "result": result, "snapshot": snap})
        await asyncio.sleep(max(0.25, 2.0 / max(0.25, sim_speed)))
    sim_running = False
    await broadcast({"type": "sim_status", "running": sim_running, "finished": sim_cursor >= len(current_events)})


def get_unified_snapshot() -> dict[str, Any]:
    snap = engine.snapshot()
    snap.update({
        "mode": operating_mode,
        "monitoring_mode": ingestion_manager.get_monitoring_mode(),
        "sources_health": ingestion_manager.get_sources_health(),
        "sources_summary": engine.source_tracker.get_summary(),
        "ingestion_running": ingestion_manager.running,
        "monitored_location": {
            "latitude": NAGPUR_CENTER_LAT,
            "longitude": NAGPUR_CENTER_LON,
            "name": f"{NAGPUR_DISTRICT_NAME}, {NAGPUR_STATE}, India",
            "district": NAGPUR_DISTRICT_NAME,
            "state": NAGPUR_STATE,
        },
        "diagnostic_excluded_count": len(ingestion_manager.diagnostic_excluded_events),
        # Simulation telemetry
        "sim_running": sim_running,
        "scenario": selected_scenario,
        "scenario_name": SCENARIOS.get(selected_scenario, "Unknown"),
        "cursor": sim_cursor,
        "total_events": len(current_events),
        "speed": sim_speed,
    })
    return snap


@asynccontextmanager
async def lifespan(app: FastAPI):
    global current_events, periodic_task
    current_events = make_scenario_events(selected_scenario, sim_seed)
    await ingestion_manager.start()
    asyncio.create_task(ingestion_manager.poll_all_sources())
    periodic_task = asyncio.create_task(minute_assessment_loop())
    yield
    if periodic_task:
        periodic_task.cancel()
    await ingestion_manager.stop()


app = FastAPI(
    title="CrisisPulse AI API: Nagpur Operational Platform",
    version="3.0.0",
    description="Live Emergency Monitoring, Predictive Intelligence, and xAI Reasoning for Nagpur.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------- Root and Health Endpoints -----------------

@app.get("/")
def root():
    return {
        "name": "CrisisPulse AI: Nagpur Live Emergency Intelligence Platform",
        "version": "3.0.0",
        "status": "operational",
        "monitoring_region": "Nagpur District & NMC Urban Area, Maharashtra, India",
        "operating_mode": operating_mode,
        "monitoring_mode": ingestion_manager.get_monitoring_mode(),
        "active_sources": [a.name for a in ingestion_manager.adapters.values() if a.enabled],
        "monitored_location": f"{NAGPUR_DISTRICT_NAME}, {NAGPUR_STATE}, India",
    }


@app.get("/api/state")
def state():
    return get_unified_snapshot()


@app.get("/api/sources")
def sources():
    return {
        "sources": ingestion_manager.get_sources_health(),
        "total_sources": len(ingestion_manager.adapters),
        "monitoring_mode": ingestion_manager.get_monitoring_mode(),
        "healthy_count": sum(1 for a in ingestion_manager.adapters.values() if a.status == "healthy"),
        "source_tracker_summary": engine.source_tracker.get_summary(),
    }


# ----------------- Nagpur Operational Geography -----------------

@app.get("/api/geography/master")
def geography_master():
    return get_nagpur_master_geojson()


@app.get("/api/geography/zones")
def geography_zones():
    return get_nagpur_zones_geojson()


@app.get("/api/geography/hotspots")
def geography_hotspots():
    return get_nagpur_hotspots_geojson()


@app.get("/api/geography/hospitals")
def geography_hospitals():
    return get_nagpur_hospitals_geojson()


@app.get("/api/geography/hydrology")
def geography_hydrology():
    return get_nagpur_hydrology_geojson()


@app.get("/api/geography/zone/{zone_id}")
@app.get("/api/region/{zone_id}")
def zone_assessment(zone_id: str):
    if zone_id not in NMC_ZONES:
        raise HTTPException(404, f"Unknown NMC Zone: {zone_id}")
    return engine.get_region_assessment(zone_id)


class XAIExplainRequest(BaseModel):
    zone_id: str = "zone-3-hanuman-nagar"


@app.post("/api/xai/explain")
def xai_explain(req: XAIExplainRequest):
    assessment = engine.get_region_assessment(req.zone_id)
    return {
        "zone_id": req.zone_id,
        "xai_explanation": assessment.get("xai_explanation"),
        "dominant_hypothesis": max(engine.probabilities, key=engine.probabilities.get),
        "probabilities": engine.probabilities.copy(),
        "action": assessment.get("action"),
    }


# ----------------- Operational Mode Switching -----------------

class ModeSwitchRequest(BaseModel):
    mode: str  # "live" or "simulation"


@app.post("/api/mode")
async def switch_mode(req: ModeSwitchRequest):
    global operating_mode, sim_running
    if req.mode not in ("live", "simulation"):
        raise HTTPException(400, "Invalid mode. Choose 'live' or 'simulation'.")
    operating_mode = req.mode
    if operating_mode == "simulation":
        sim_running = False
    snap = get_unified_snapshot()
    await broadcast({"type": "mode_change", "mode": operating_mode, "snapshot": snap})
    return {"mode": operating_mode, "snapshot": snap}


# ----------------- Manual Feeds Polling -----------------

@app.post("/api/poll")
async def poll_feeds(source: str | None = None):
    if source:
        events = await ingestion_manager.poll_source(source)
        return {"source": source, "records_ingested": len(events)}
    results = await ingestion_manager.poll_all_sources()
    return {"status": "polled_all", "summary": results}


# ----------------- The Twin Test & Intelligence Lab -----------------

@app.get("/api/twin-test")
@app.get("/api/lab/twin-test")
def api_twin_test(seed: int = 42):
    return lab.run_twin_test(seed=seed)


@app.get("/api/lab/replay")
def lab_replay(scenario: str = "cascade", seed: int = 42):
    return lab.replay_sequence(scenario_name=scenario, seed=seed)


class CounterfactualRequest(BaseModel):
    counterfactual_type: str


@app.post("/api/lab/counterfactual")
def lab_counterfactual(req: CounterfactualRequest):
    return lab.run_counterfactual(
        base_probabilities=engine.probabilities.copy(),
        counterfactual_type=req.counterfactual_type,
    )


# ----------------- Online Source Trust Learning Endpoints -----------------

class VerificationOutcomeRequest(BaseModel):
    source_id: str
    category: str = "general"
    was_accurate: bool
    authoritative_source: str = "District Emergency Operations Center (EOC)"
    latency_sec: float = 0.0


@app.post("/api/learning/verify")
def record_verification(req: VerificationOutcomeRequest):
    return engine.online_learner.record_verification_outcome(
        source_id=req.source_id,
        category=req.category,
        was_accurate=req.was_accurate,
        authoritative_source=req.authoritative_source,
        verification_latency_sec=req.latency_sec,
    )


class TrustExperimentRequest(BaseModel):
    source_id: str
    episode_sequence: list[bool] = [True, True, False, True, True]


@app.post("/api/learning/experiment")
def run_trust_experiment(req: TrustExperimentRequest):
    return engine.online_learner.run_controlled_trust_experiment(
        source_id=req.source_id,
        episode_sequence=req.episode_sequence,
    )


@app.get("/api/learning/log")
def get_learning_log(limit: int = 50):
    return engine.online_learner.get_audit_log(limit=limit)


# ----------------- Base-Rate Adaptation Endpoints -----------------

@app.get("/api/base-rate/drift")
def get_base_rate_drift():
    return {
        "priors": engine.base_rate_adapter.get_current_priors(include_aliases=True),
        "drift_status": engine.base_rate_adapter.update_environmental_drift(0.0),
        "total_verified_outcomes": engine.base_rate_adapter.total_verified,
        "verified_outcomes_by_hypothesis": engine.base_rate_adapter.verified_outcomes_count,
    }


class VerifiedOutcomeRequest(BaseModel):
    true_hypothesis: str


@app.post("/api/base-rate/adapt")
def adapt_base_rate(req: VerifiedOutcomeRequest):
    res = engine.base_rate_adapter.record_verified_outcome(req.true_hypothesis)
    engine.bayesian.default_priors = engine.base_rate_adapter.get_current_priors(include_aliases=True)
    return res


# ----------------- Retraction & Correction Audit -----------------

@app.get("/api/retractions/audit")
def get_retraction_audit():
    return {
        "retracted_event_ids": list(engine.retraction_manager.retracted_event_ids),
        "superseded_event_ids": engine.retraction_manager.superseded_event_ids,
        "audit_log": engine.retraction_manager.retraction_audit_log,
    }


# ----------------- Model Evaluation -----------------

@app.post("/api/evaluation/run")
def run_evaluation():
    report = evaluator.run_benchmark_evaluation(runs_per_scenario=3)
    m = report["metrics"]
    db.record_evaluation(
        run_id=report["evaluation_id"],
        dataset_name=report["benchmark_dataset"],
        sample_count=report["sample_scenario_runs"],
        precision=m["precision"],
        recall=m["recall"],
        f1=m["f1_score"],
        far=m["false_alarm_rate"],
        mr=m["missed_crisis_rate"],
        brier=m["brier_score"],
        lead_time=m["average_lead_time_minutes"],
        period=report["evaluation_period"],
    )
    return report


@app.get("/api/evaluation/latest")
def latest_evaluation():
    return evaluator.run_benchmark_evaluation(runs_per_scenario=2)


# ----------------- Simulation Endpoints -----------------

@app.get("/api/scenarios")
def scenarios():
    return [{"id": k, "name": v} for k, v in SCENARIOS.items()]


@app.post("/api/start")
async def start_simulation():
    global sim_running, simulation_task
    if sim_cursor >= len(current_events):
        raise HTTPException(400, "Scenario complete. Reset to replay.")
    if not sim_running:
        sim_running = True
        simulation_task = asyncio.create_task(simulation_loop())
    return {"running": sim_running}


@app.post("/api/pause")
async def pause_simulation():
    global sim_running
    sim_running = False
    return {"running": sim_running}


@app.post("/api/reset")
async def reset_simulation():
    global sim_running, sim_cursor, current_events
    sim_running = False
    engine.reset()
    sim_cursor = 0
    current_events = make_scenario_events(selected_scenario, sim_seed)
    snap = get_unified_snapshot()
    await broadcast({"type": "reset", "snapshot": snap})
    return {"ok": True, "snapshot": snap}


@app.post("/api/scenario/{scenario_id}")
async def choose_scenario(scenario_id: str):
    global selected_scenario, sim_running, sim_cursor, current_events
    if scenario_id not in SCENARIOS:
        raise HTTPException(404, "Unknown scenario")
    sim_running = False
    selected_scenario = scenario_id
    engine.reset()
    sim_cursor = 0
    current_events = make_scenario_events(selected_scenario, sim_seed)
    snap = get_unified_snapshot()
    await broadcast({"type": "reset", "snapshot": snap})
    return {"scenario": selected_scenario, "snapshot": snap}


@app.post("/api/speed/{value}")
def set_speed(value: float):
    global sim_speed
    sim_speed = min(4.0, max(0.25, value))
    return {"speed": sim_speed}


@app.post("/api/inject/gateway-failure")
async def inject_gateway_failure():
    event = Event(
        event_id=f"manual-gateway-{engine.tick}",
        event_type="gateway_failure",
        source_id="manual-gateway-controller",
        gateway_id="water-gw",
        severity=0.95,
        reliability=0.95,
        payload={"operator_injected": True},
    )
    result = engine.process(event)
    snap = get_unified_snapshot()
    await broadcast({"type": "update", "result": result, "snapshot": snap})
    return result


@app.post("/api/inject/duplicate")
async def inject_duplicate():
    if not engine.events:
        raise HTTPException(400, "No event available to duplicate yet.")
    old = engine.events[0]
    event = Event(
        event_id=old["event_id"],
        event_type=old["event_type"],
        source_id=old["source_id"],
        zone_id=old["zone_id"],
        severity=old["severity"],
        reliability=old["reliability"],
    )
    result = engine.process(event)
    return result


@app.get("/api/export")
def export_state():
    return {
        "operating_mode": operating_mode,
        "monitored_region": f"{NAGPUR_DISTRICT_NAME}, {NAGPUR_STATE}, India",
        "snapshot": get_unified_snapshot(),
        "audit_ledger": db.get_audit_ledger(limit=100),
        "source_health": ingestion_manager.get_sources_health(),
        "database_records_count": len(db.get_events(limit=1000)),
        "system_notice": "CrisisPulse AI Nagpur operational telemetry report. Non-autonomous decision support.",
    }


# ----------------- WebSocket Live Stream -----------------

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    await ws.send_json({"type": "init", "snapshot": get_unified_snapshot()})
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        clients.discard(ws)
