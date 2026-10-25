# CrisisPulse AI: Nagpur Live Emergency Intelligence Platform
## Codebase & Architectural Audit

**Audit Date:** 2026-10-25  
**Auditor:** Senior Full-Stack & AI/ML Systems Engineer  
**Target Operational Region:** Nagpur District & Nagpur Municipal Corporation (NMC), Maharashtra, India  
**Target Version:** CrisisPulse AI 2.5 (Nagpur Operational Edition)

---

### 1. Executive Summary

CrisisPulse AI was originally prototyped as a dual-mode emergency decision-support dashboard featuring Bayesian hypothesis updating, anomaly detection, expected-loss decision logic (WATCH, PREPARE, ALERT, ESCALATE), and a First-10-Minute Intelligence Lab. 

While the probabilistic framework and fast UI prototyping are solid, **the existing codebase cannot operate as a Nagpur emergency intelligence platform without substantial architectural transformation**:
1. **Geographic Inaccuracy:** Default configurations, adapters, schemas, and fallback coordinates were hardcoded to **Mumbai, India** (`19.0760° N, 72.8777° E`).
2. **Global Event Leakage:** Global USGS earthquakes (e.g., California, Indonesia) and global GDACS bulletins were ingested directly into the local operational state without spatial relevance filtering or impact radius checks for Nagpur.
3. **Absence of Authoritative Nagpur Geometry:** There was no representation of Nagpur district boundaries, Nagpur Municipal Corporation (NMC) 10 administrative zones, 38 Prabhags / 151+ Wards, or known waterlogging hotspots (e.g., Narendra Nagar, Mor Bhavan, Besa-Ghogli, Pardi, Ambazari Lake catchment).
4. **Data Integrity & False "LIVE" Labels:** `regional_india.py` only pinged the NDMA Sachet portal URL without parsing data, returning an empty list. NASA FIRMS fell back silently to a sample JSON without distinguishing synthetic/sample records from live telemetry. The UI displayed a bright green "STREAM LIVE" dot regardless of whether data feeds were stale, cached, or fallback.
5. **Missing xAI Integration:** No xAI (Grok) client existed in the codebase. Explanations were rudimentary string concatenations rather than structured, evidence-grounded reasoning.
6. **Lack of Municipal Infrastructure Providers:** There were no clean provider interfaces or schemas for Nagpur Municipal Corporation (NMC) stormwater drainage, hospital emergency capacity, or traffic congestion/closures.

---

### 2. Architectural Audit by Component

#### 2.1 Backend Architecture (FastAPI & Python 3.13)
- **Application Core (`backend/app/main.py`):** FastAPI app with lifespan hooks, WebSockets, background ingestion loop, simulation state machine, and REST endpoints.
  - *Strengths:* Clean modular separation of inference engine, database, and ingestion manager.
  - *Weaknesses:* Background tasks blindly poll global endpoints on startup; tests hang in sandboxed environments if network calls are unmocked; hardcoded virtual environment paths from previous developer machine (`C:\Python313\python.exe` and OneDrive).
- **Inference Engine (`backend/app/engine.py`):** Coordinates Bayesian updating, anomaly detection, decision thresholds, and ledger persistence.
  - *Strengths:* Mathematically sound 4-hypothesis space (`normal`, `source_failure`, `isolated_incident`, `cascading_crisis`), tempered likelihood updating ($L^{\alpha}$), and expected-cost matrix.
  - *Weaknesses:* Hardcoded Mumbai coordinates (19.076, 72.877) in fallback event constructors; single global state rather than subregion-aware (district vs. ward) spatial state.
- **Normalization & Schemas (`backend/app/normalization/schema.py`, `schemas.py`):**
  - Unified `NormalizedEvent` schema with spatial attributes.
  - *Gaps:* Missing explicit provenance flags (`LIVE`, `FORECAST`, `HISTORICAL`, `CACHED`, `UNVERIFIED`, `SYNTHETIC`), missing geographic precision flags (`exact`, `approximate`, `district_level`, `ward_level`), and missing Nagpur administrative zone bindings.

#### 2.2 Data Ingestion & Connector Audit
- **Open-Meteo (`backend/app/ingestion/open_meteo.py`):**
  - Fetches temperature, precipitation, wind speed, wind gusts, weather code, pressure, and humidity.
  - *Issue:* Weather forecasts and instantaneous precipitation need clear labeling so forecasts are never disguised as verified ground rainfall.
- **IMD & Regional India (`backend/app/ingestion/regional_india.py`):**
  - Stated to ingest IMD and NDMA, but merely executed an HTTP GET to `sachet.ndma.gov.in` and returned `[]`.
  - *Requirement:* Implement a genuine IMD / RMC Nagpur weather and warning connector following `https://api.imd.gov.in/public/api_reference.html` schema (district rainfall, nowcast warnings, AWS/ARG observations) with environment-based authentication and offline resilience.
- **USGS Earthquake (`backend/app/ingestion/usgs_earthquake.py`):**
  - Fetches global earthquakes $M \ge 2.0$ or $4.5$.
  - *Issue:* Earthquakes thousands of kilometers away in California or the Pacific Rim were ingested and updated the local belief state! Must implement a distance/impact bounding filter centered on Nagpur (~300 km regional seismic impact threshold, or felt-intensity modeling).
- **GDACS Alerts (`backend/app/ingestion/gdacs.py`):**
  - Parses RSS feeds globally.
  - *Issue:* Global floods and cyclones in other continents were processed into the active event queue. Must filter by geographic bounding box and India/Maharashtra relevance.
- **NASA FIRMS (`backend/app/ingestion/nasa_firms.py`):**
  - Queries VIIRS active fires for country code `IND`.
  - *Issue:* Without an API key, it loaded a sample JSON from an unspecified location and labeled it with preliminary status. Must be filtered specifically to the Nagpur district bounding box (`20.5° N` to `21.8° N`, `78.2° E` to `79.7° E`) and clearly labeled with satellite detection latency and provenance (`LIVE` vs `CACHED_SAMPLE`).
- **Missing Domain Connectors:**
  - Hospital Emergency Operations (bed capacity, emergency department surge, ambulance dispatch delays).
  - Municipal Drainage & Waterlogging (NMC major nullahs, Nag river, Pili river, Pora river, known chronic waterlogging junctions).
  - Traffic & Road Chokepoints (critical ambulance corridors, submerged underpasses).

#### 2.3 Decision Logic & Response Classification
- **Decision Engine (`backend/app/decision_engine/decider.py`):**
  - Maps 4 Bayesian posterior probabilities to expected loss across `WATCH`, `PREPARE`, `ALERT`, `ESCALATE`.
  - Gated escalation: ESCALATE requires $P(\text{cascade}) \ge 0.70$ and $\ge 2$ independent corroborated sources.
  - *Strengths:* Transparent cost matrix, clear gating preventing autonomous false alarms.
  - *Improvement:* Add Nagpur-specific subregion risk aggregation, rate-of-change safeguards against flapping, and clear distinction between probability, severity, data quality, and operational priority.

#### 2.4 Explainability & xAI (Grok) Layer
- **Current State:** Non-existent. The engine called a simple string formatter `engine.explain()` with fixed sentences.
- *Requirement:* Implement an official xAI integration (`https://docs.x.ai/`) using `XAI_API_KEY`, sending structured evidence packets (evidence, source reliability, timestamps, contradictory reports, missing data) and validating JSON responses against strict Pydantic schemas. Gracefully fallback to deterministic evidence-grounded templates when keys are absent or API is unreachable.

#### 2.5 GIS & Frontend Dashboard (`frontend/src/`)
- **Map Component (`components/Map.tsx`):**
  - Basic Leaflet map with global CartoDB tiles and generic point markers.
  - *Gaps:* No GeoJSON polygon boundaries for Nagpur District, NMC urban area, or the 10 administrative zones (Laxmi Nagar, Dharampeth, Hanuman Nagar, Dhantoli, Nehru Nagar, Gandhibagh, Satranjipura, Lakadganj, Ashi Nagar, Mangalwari). No ward-level drill-down. No layer for chronic flood hotspots or hospital hubs.
- **Dashboard Layout (`App.tsx` & `style.css`):**
  - Generic emergency dashboard with simulation presets.
  - *Requirement:* Transform into a Nagpur Command-Center Dashboard featuring an operational header, Nagpur district & zone risk overview, live filtered intelligence feed with verifiable provenance, prominent **"WHY DOES CRISISPULSE BELIEVE THIS AREA IS AT RISK?"** xAI panel, multi-horizon forecast timeline, and data connector health monitor.

---

### 3. Immediate Action Plan (Execution Order)

1. **Centralized Nagpur Geographic Layer (`backend/app/geography/` & `data/geography/`):**
   - Authoritative GeoJSON boundaries for Nagpur District and Nagpur City (NMC).
   - Zone and ward registry (10 municipal zones, key localities, and chronic waterlogging hotspots).
   - Strict spatial filter: point-in-polygon and bounding-box relevance checks for all incoming observations.
2. **Modular Data Providers & Real Nagpur Ingestion (`backend/app/ingestion/`):**
   - Open-Meteo configured specifically for Nagpur coordinates (`21.1458° N, 79.0882° E`) with explicit observation vs forecast separation.
   - IMD / RMC Nagpur weather & severe-weather warning connector with official schema support and environment authentication.
   - Spatial filtering for USGS and GDACS (rejecting out-of-region events).
   - NASA FIRMS filtered strictly to Nagpur district coordinates.
   - Clean provider interfaces for Hospital Capacity, NMC Drainage / Waterlogging, and Road Traffic.
   - Centralized health, freshness, and provenance telemetry (`LIVE`, `FORECAST`, `CACHED`, `UNVERIFIED`, `SYNTHETIC`).
3. **Evidence-Grounded xAI Explanation Engine (`backend/app/xai/`):**
   - xAI client adhering to official API specifications (`https://api.x.ai/v1/chat/completions`).
   - Compact structured evidence packet generator.
   - Schema validation for xAI responses.
   - Deterministic evidence-grounded fallback.
4. **Subregion Risk Assessment & Multi-Horizon Forecasting:**
   - Zone-by-zone and district-wide risk calculation.
   - 10-min, 30-min, and 60-min horizon forecasts with explicit uncertainty and limitations.
   - Event correlation & cascading dependency tracking.
5. **Frontend Redesign (Nagpur Operational Command Center):**
   - Professional dark command-center aesthetic.
   - Interactive Nagpur GIS Map with District & Zone polygons, hotspot markers, and layer toggles.
   - Area selection detail panel with live evidence and drill-down.
   - Explanatory panel: "WHY DOES CRISISPULSE BELIEVE THIS AREA IS AT RISK?".
   - Operational header with data freshness, active event counts, and monitoring modes.
6. **Testing, Validation & Documentation:**
   - Unit and integration tests for geographic filtering, IMD parsing, xAI grounding, and decision thresholds.
   - Frontend TypeScript check and production build verification.
   - Comprehensive documentation (`README.md`, `HANDOFF.md`, `docs/data_sources.md`, `docs/api_contract.md`, `docs/model_assumptions.md`, `docs/geographic_data.md`, `docs/testing.md`).
