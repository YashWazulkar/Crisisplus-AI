# CrisisPulse AI · Test Suite & Verification Guide

This document details the test architecture, test suites, and procedures for verifying CrisisPulse AI across the backend inference engine, data ingestion pipelines, geographic boundaries, explainability subsystems, and frontend client.

---

## 1. Quick Test Execution

### 1.1 Backend Test Suite (Pytest)
Run the complete backend test suite from the repository root:

```bash
# Using python -m pytest
python -m pytest crisispulse-ai-base/backend/tests -v

# Run with verbose output and timing
python -m pytest crisispulse-ai-base/backend/tests -v --durations=10
```

### 1.2 Frontend Build & Typecheck (Vite & TypeScript)
Verify frontend TypeScript types and compile the production bundle:

```bash
cd crisispulse-ai-base/frontend
npm run build
```

---

## 2. Backend Test Architecture (37 Automated Tests)

The backend test suite contains **37 unit and integration tests** organized into 8 focused modules:

```
crisispulse-ai-base/backend/tests/
├── test_adapters.py                  # 9 tests: Ingestion adapters & provider connectors
├── test_api.py                       # 6 tests: REST endpoints & JSON contracts
├── test_engine.py                    # 3 tests: Belief updates, deduplication, invariants
├── test_geography.py                 # 6 tests: Spatial filtering, zones, GeoJSON layers
├── test_inference_and_decisions.py   # 3 tests: Tempered Bayes, MAD anomaly, decision gates
├── test_lab_and_evaluation.py        # 4 tests: Replay lab, twin tests, counterfactuals, metrics
├── test_pipeline.py                  # 3 tests: Bounds validation, deduplication, quality
└── test_xai.py                       # 3 tests: Grok integration, grounding validator, fallback
```

---

## 3. Test Module Details

### 3.1 `test_adapters.py` (9 Tests)
- `test_open_meteo_adapter_parsing`: Validates live telemetry parsing and separation of numerical forecasts (`FORECAST` provenance).
- `test_open_meteo_adapter_error_handling`: Validates timeout handling and fallback to previous observations without crashing.
- `test_imd_adapter_reference_and_live_parsing`: Validates parsing of RMC Nagpur weather bulletins, color code severity mapping (`GREEN`, `YELLOW`, `ORANGE`, `RED`), and `awaiting_api_credentials` transparent fallback.
- `test_drainage_provider_hotspot_threshold_evaluation`: Validates waterlogging evaluation against Narendra Nagar and Ambazari rainfall thresholds.
- `test_hospital_provider_baseline`: Validates GMCH Nagpur trauma capacity calculation and mass casualty diversion alerts.
- `test_traffic_provider_corridor_disruption`: Validates Wardha Road and underpass flood transit speed drops and ambulance delays.
- `test_usgs_earthquake_filtering_for_nagpur`: Verifies out-of-region global quakes (e.g. Chile, Japan) are rejected while regional Central India quakes are preserved.
- `test_gdacs_adapter_parsing_and_filtering`: Verifies exclusion of non-impacting global alerts.
- `test_nasa_firms_fallback_sample`: Verifies VIIRS thermal anomaly processing and transparent reference fallback mode.

### 3.2 `test_geography.py` (6 Tests)
- `test_nagpur_zones_structure`: Validates 10 NMC administrative zones, Marathi names, centroids, and chronic hotspots.
- `test_spatial_filter_urban_nagpur`: Verifies point-in-polygon ray-casting assigns Sitabuldi coordinates to Dhantoli (`zone_4`).
- `test_spatial_filter_district_level_separation`: Verifies rural/district events are labeled `district_level` and never falsely localized to a municipal ward.
- `test_spatial_filter_excludes_out_of_region`: Validates rejection of coordinates outside Nagpur District (e.g. Mumbai, Delhi, Tokyo).
- `test_spatial_filter_downstream_impact`: Verifies regional earthquakes ($M \ge 4.0$) within 300 km are retained with downstream flags.
- `test_geojson_master_generation`: Validates structural integrity of GeoJSON FeatureCollections for district, urban, zones, hotspots, and rivers.

### 3.3 `test_xai.py` (3 Tests)
- `test_deterministic_explanation_synthesis`: Verifies rule-based grounded explanation synthesizer produces compliant natural language without external API keys.
- `test_grounding_validator_prevents_override`: Asserts `XAIGroundingValidator` rejects LLM hallucinations that contradict backend action postures or invent unsupported data feeds.
- `test_xai_client_fallback_when_unconfigured`: Verifies `XAIClient` gracefully falls back to deterministic synthesis when `XAI_API_KEY` is empty.

### 3.4 `test_inference_and_decisions.py` (3 Tests)
- `test_bayesian_updates_and_tempering`: Validates evidence tempering weight $\omega \in [0.05, 1.0]$ and freshness decay.
- `test_anomaly_detector_mad_robust_z`: Validates Median Absolute Deviation calculation and `Robust Z >= 3.0` trigger.
- `test_decision_engine_cautious_escalation_gate`: Asserts that `ESCALATE` action cannot be reached without meeting both probability ($P(H_4) \ge 0.70$) and multi-source corroboration gates.

### 3.5 `test_lab_and_evaluation.py` (4 Tests)
- `test_intelligence_lab_minute_by_minute_replay`: Replays 10-minute monsoon scenario tick by tick.
- `test_intelligence_lab_twin_test_divergence`: Verifies twin test divergence between baseline and synthetic sensor failure.
- `test_intelligence_lab_counterfactual_analysis`: Tests counterfactual scenario evaluation by toggling critical observations.
- `test_model_evaluation_metrics`: Calculates Brier score, Expected Calibration Error (ECE), and log loss against ground truth.

---

## 4. Test Pass Invariants

When running the suite, verify that all assertions satisfy these core invariants:
1. **Belief Normalization:** $\sum_{i=1}^4 P(H_i) = 1.0 \pm 10^{-6}$ at every step.
2. **Provenance Integrity:** No synthetic or cached event is ever assigned `data_provenance = LIVE`.
3. **Spatial Precision:** Coordinates outside NMC zones are never assigned a `zone_id`.
4. **Deterministic Fallbacks:** The entire system functions without network connectivity or API keys.
