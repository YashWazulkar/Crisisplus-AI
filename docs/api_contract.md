# CrisisPulse AI · API Contract & Integration Specification

This document defines the REST and WebSocket API interfaces provided by the CrisisPulse AI backend.

---

## 1. REST API Endpoints

### 1.1 Core System & State

#### `GET /health`
Returns system liveness and basic process uptime.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "crisispulse-ai",
  "version": "2.0.0",
  "region": "Nagpur District, Maharashtra"
}
```

#### `GET /api/status`
Provides lightweight operational health, active mode, and connector connectivity counters.
- **Response `200 OK`**:
```json
{
  "status": "online",
  "mode": "live",
  "monitoring_mode": "MIXED",
  "action": "WATCH",
  "active_events_count": 5,
  "sources_healthy": 6,
  "sources_total": 8,
  "timestamp": "2026-10-25T14:30:00.000000+00:00"
}
```

#### `GET /api/state`
Returns the complete operational state snapshot, including Bayesian probabilities, active observations, decision ledger, near-term forecasts, xAI explanation, and subregion risks.
- **Response `200 OK`**:
```json
{
  "action": "WATCH",
  "mode": "live",
  "monitoring_mode": "MIXED",
  "probabilities": {
    "normal": 0.582,
    "source_failure": 0.081,
    "isolated_incident": 0.234,
    "cascading_crisis": 0.103
  },
  "expected_loss": 0.312,
  "events": [...],
  "event_counts": {
    "total_active": 6,
    "verified": 4,
    "unverified": 2
  },
  "sources_health": [...],
  "risk_overview": {
    "current_hazard": "Urban Waterlogging & Monsoon Inundation",
    "most_affected_area": "Zone 4 - Dhantoli (Narendra Nagar)",
    "hazard_category": "drainage",
    "event_probability": 0.72,
    "severity": 0.75,
    "evidence_quality": 0.91,
    "uncertainty": "Low",
    "response_recommendation": "Activate stormwater pumps and deploy traffic wardens at Narendra Nagar underpass.",
    "primary_evidence": "IMD Yellow Convective Warning & 48mm/h precipitation at Narendra Nagar"
  },
  "xai_explanation": {
    "decision_rationale": "...",
    "primary_driver": "Monsoon underpass inundation",
    "evidence_synthesis": "...",
    "subregion_analysis": [...],
    "grounding_status": "fully_grounded"
  },
  "subregions": {
    "zone_4": {
      "zone_id": "zone_4",
      "zone_name": "Dhantoli",
      "marathi_name": "धंतोली",
      "risk_level": "ALERT",
      "active_events_count": 2,
      "hotspots_at_risk": ["Narendra Nagar Railway Underpass"]
    }
  },
  "forecasts": [...],
  "ledger": [...]
}
```

---

### 1.2 Nagpur Geographic & Administrative Boundaries

#### `GET /api/geography/master`
Returns the combined GeoJSON master dataset containing District boundaries, Municipal boundaries, 10 Administrative Zones, Chronic Hotspots, Hospitals, and Hydrological River Corridors.
- **Response `200 OK`**:
```json
{
  "district_boundary": { "type": "FeatureCollection", "features": [...] },
  "urban_boundary": { "type": "FeatureCollection", "features": [...] },
  "zones": { "type": "FeatureCollection", "features": [...] },
  "hotspots": { "type": "FeatureCollection", "features": [...] },
  "hospitals": { "type": "FeatureCollection", "features": [...] },
  "hydrology": { "type": "FeatureCollection", "features": [...] }
}
```

#### `GET /api/geography/zones`
Returns the FeatureCollection for the 10 official NMC administrative zones with centroid coordinates, population, and Marathi transliterations.

#### `GET /api/geography/hotspots`
Returns Point features for the 7 chronic waterlogging hotspots in Nagpur with critical submersion rainfall thresholds.

#### `GET /api/geography/hospitals`
Returns Point features for the 6 emergency trauma and referral hospitals in Nagpur with normal bed capacities.

#### `GET /api/region/{zone_id}`
Returns granular telemetry, chronic hotspots, active events, and localized forecast assessments for a specific NMC zone (e.g. `zone_3`, `zone_4`).
- **Path Parameter:** `zone_id` (`zone_1` through `zone_10`)
- **Response `200 OK`**:
```json
{
  "zone_id": "zone_4",
  "zone_name": "Dhantoli",
  "marathi_name": "धंतोली",
  "risk_level": "ALERT",
  "active_events": [...],
  "hotspots": [
    {
      "id": "hotspot_narendra_nagar",
      "name": "Narendra Nagar Railway Underpass",
      "critical_threshold_mm_h": 25.0,
      "current_status": "submerged_impassable"
    }
  ],
  "hospitals": [...],
  "population_estimate": 240000,
  "recommendations": [...]
}
```

---

### 1.3 Explainable AI (xAI) Interface

#### `POST /api/xai/explain`
Generates an evidence-grounded explanation from the current operational evidence packet using xAI Grok (or the deterministic synthesizer fallback).
- **Request Body (Optional overrides):**
```json
{
  "zone_id": "zone_4"
}
```
- **Response `200 OK`**:
```json
{
  "action": "ALERT",
  "primary_driver": "Narendra Nagar Underpass Submersion",
  "decision_rationale": "High-intensity rainfall (48 mm/h) exceeds the 25 mm/h drainage capacity at Narendra Nagar underpass, causing traffic blockage along the Wardha Road ambulance corridor.",
  "evidence_synthesis": "Corroborated by IMD Yellow convective alert and NMC water level sensor reading 0.85m depth.",
  "contradictory_evidence_analysis": "No conflicting reports; satellite thermal pass confirms no unrelated industrial fires in the vicinity.",
  "missing_data_disclosure": "Pora river sensor node at Manewada is reporting with an 8-minute latency.",
  "subregion_analysis": [...],
  "human_decision_guidance": [
    "Divert Southbound emergency traffic via Ring Road Flyover.",
    "Do not dispatch field crews into submerged culvert without de-energizing local utility lines."
  ],
  "grounding_status": "fully_grounded",
  "model_identifier": "grok-2-1212"
}
```

---

### 1.4 System Controls & Simulation Lab

#### `POST /api/mode`
Switches operational runtime between live external telemetry and lab benchmark simulation.
- **Request Body:**
```json
{
  "mode": "live"
}
```

#### `POST /api/poll`
Forces immediate ingestion polling of a specific connector or all connectors.
- **Request Body:**
```json
{
  "source_name": "imd-nagpur"
}
```

#### `POST /api/reset`
Clears active observations, Bayesian event ledger, and resets belief states to baseline priors.

#### `POST /api/evaluate`
Executes model performance benchmark against synthetic and historical ground-truth incident records.
- **Response `200 OK`**:
```json
{
  "brier_score": 0.082,
  "log_loss": 0.241,
  "ece": 0.054,
  "accuracy": 0.94,
  "lead_time_minutes": 18.5,
  "total_evaluations": 500
}
```

#### `POST /api/lab/run`
Executes a First-10-Minute minute-by-minute benchmark scenario for emergency training.
- **Request Body:**
```json
{
  "scenario_id": "nagpur_monsoon_flash_flood",
  "speed_multiplier": 1.0
}
```

---

## 2. WebSocket Real-Time Interface

### Endpoint: `ws://{HOST}:{PORT}/ws`
The WebSocket interface pushes instantaneous state transitions, incoming observations, and telemetry updates to connected command-center clients without client-side polling.

#### Client Connection Lifecycle
1. **Connect:** Client initiates WebSocket handshake.
2. **Initial Snapshot:** Server transmits complete initial state snapshot (`type: "INITIAL_STATE"`).
3. **Event Stream:** As adapters ingest data or decision states change, server broadcasts delta messages:
   - `type: "EVENT_INGESTED"`: New validated observation.
   - `type: "STATE_UPDATE"`: Updated Bayesian posterior and action.
   - `type: "FORECAST_UPDATE"`: Updated 10/30/60m projections.
   - `type: "SOURCE_HEALTH"`: Connectivity status change.
4. **Heartbeat:** Ping/pong frames keep connection alive every 30 seconds.
