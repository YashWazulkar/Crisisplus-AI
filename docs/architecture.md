# CrisisPulse AI 2.0 — System Architecture

## 1. Executive Architecture Summary

CrisisPulse AI 2.0 is an end-to-end, real-time emergency monitoring, probabilistic inference, and short-horizon predictive intelligence platform. Built specifically for the hackathon challenge **“The First 10 Minutes”**, it ingests real live signals from public meteorological, seismic, wildfire, and multi-hazard alert feeds, processes them through an evidentiary pipeline, dynamically updates Bayesian hypothesis distributions, and delivers cost-optimal, explainable response recommendations.

```text
                                  EXTERNAL SOURCES
  [ Open-Meteo Weather ]    [ USGS Earthquakes ]    [ GDACS Multi-Hazard ]    [ NASA FIRMS Fires ]
           │                         │                        │                        │
           └─────────────────────────┼────────────────────────┼────────────────────────┘
                                     ▼
                        [ Ingestion Adapters Layer ]
                      (Rate Limits, Retries, Exponential Backoff)
                                     ▼
                     [ Validation & Normalization Pipeline ]
                     (Bounds Checking, Spatio-Temporal Dedup,
                       Quality & Freshness Decay Scoring)
                                     ▼
                     [ Intelligence & Inference Engine ]
    ┌────────────────────────────────┼────────────────────────────────┐
    ▼                                ▼                                ▼
[ Bayesian Belief Engine ]   [ Anomaly Detector ]        [ Causal Cascade Graph ]
(H1: Normal                  (Robust Z / MAD             (Physical & Logistics
 H2: Source Failure           Spatial Cluster Swarms)     Propagation Pathways)
 H3: Isolated Incident
 H4: Cascading Crisis)
    │                                │                                │
    └────────────────────────────────┼────────────────────────────────┘
                                     ▼
                      [ Predictive Forecasting Engine ]
                         (10m, 30m, 60m Horizons)
                                     ▼
                        [ Alert & Decision Engine ]
                   (Cost Loss Matrix + Corroboration Gates)
                     WATCH · PREPARE · ALERT · ESCALATE
                                     ▼
                ┌────────────────────┴────────────────────┐
                ▼                                         ▼
      [ SQLite Persistence ]                 [ Live WebSocket Broadcast ]
  (Events, Ledgers, Hypotheses)                           ▼
                                            [ React Operations Dashboard ]
                                       (Interactive Leaflet Map, Twin Test,
                                        What-If Simulator, Audit Ledger)
```

## 2. Pipeline Stages

1. **Ingestion Adapters (`app/ingestion/`)**:
   - `OpenMeteoAdapter`: Atmospheric telemetry (precipitation rate, wind gusts, temperature, atmospheric surface pressure, WMO weather classifications). Dynamic city geocoding support.
   - `USGSEarthquakeAdapter`: USGS Earthquake Hazards feed (`all_hour.geojson` with `all_day.geojson` fallback). Hypocenter depth, Richter magnitude, PAGER alert tier, and tsunami flag extraction.
   - `GDACSAdapter`: UN/EC Global Disaster Alert Coordination System real-time RSS feed parsing tropical cyclones, floods, earthquakes, and volcanic events.
   - `NASAFIRMSAdapter`: VIIRS satellite active fire hotspots, Fire Radiative Power (MW), and brightness temperature anomalies. Gracefully falls back to bundled verified reference samples if `FIRMS_MAP_KEY` is omitted.
   - `RegionalIndiaAdapter`: Official IMD and NDMA Sachet disaster portal monitoring with configurable government SSL certificate handling.

2. **Validation (`app/validation/validator.py`)**:
   - Rejects physically impossible geographic coordinates ($\text{lat} \notin [-90, 90]$, $\text{lon} \notin [-180, 180]$).
   - Enforces temporal sanity (flags clock drift beyond 15 minutes, rejects invalid future timestamps).
   - Bounds-checks physical telemetry (non-negative rainfall, valid magnitude scales).

3. **Deduplication & Correlation (`app/deduplication/deduplicator.py`)**:
   - Prevents duplicate insertion of upstream event identifiers (`external_id`).
   - Sifts spatio-temporally correlated observations (events within 15 km radius and 15 minute window) to avoid violating Bayesian independence assumptions.

4. **Data Quality & Trust Scoring (`app/data_quality/scorer.py`)**:
   - Computes dynamic evidence quality weight $\omega \in [0.05, 1.0]$.
   - Applies exponential temporal freshness decay: $\omega_{\text{freshness}} = \exp(-\ln(2) \cdot \Delta t / t_{1/2})$.
   - Penalizes unverified reports, single-sensor gateway clusters, and diagnostic anomaly flags.

5. **Bayesian Probabilistic Inference (`app/inference/bayesian.py`)**:
   - Maintains belief distribution across 4 mutually exclusive hypotheses:
     - $H_1$: Normal conditions
     - $H_2$: Data-source or sensor failure
     - $H_3$: Isolated incident
     - $H_4$: Potential cascading emergency
   - Computes tempered Bayesian likelihood updates:
     $$P(H_i | E) \propto P(H_i) \cdot \left[ P(E | H_i) \right]^\omega$$
   - Enforces a Dirichlet smoother / prior floor ($\epsilon = 0.035$) to prevent hypothesis starvation or zero-probability lock under temporary noise bursts.

6. **Anomaly Detection (`app/inference/anomaly_detector.py`)**:
   - Calculates robust Z-scores using Median and Median Absolute Deviation (MAD):
     $$\text{Robust } Z = \frac{x - \text{median}}{1.4826 \times \text{MAD}}$$
   - Flags sudden cloudburst spikes, gale-force wind shifts, and high-magnitude seismic shocks.
   - Detects geographic incident swarms using Haversine spatial clustering ($>3$ co-located incidents within 35 km).

7. **Causal Dependency Graph (`app/causal_analysis/graph.py`)**:
   - Directed acyclic graph mapping inter-domain cascading mechanisms:
     $$\text{Severe Rain} \longrightarrow \text{Drainage Surcharge} \longrightarrow \text{Road Submersion} \longrightarrow \text{Gridlock} \longrightarrow \text{Ambulance Delay} \longrightarrow \text{Hospital Surge}$$
   - Dynamically computes activation confidence and expected propagation latencies.

8. **Decision Engine & Evidence Gating (`app/decision_engine/decider.py`)**:
   - Evaluates expected cost across 4 operational response levels:
     $$\text{Cost}(A) = \sum_{h \in \text{Hypotheses}} P(h) \cdot \text{Loss}(A, h)$$
   - Enforces a strict evidence gate: escalation to **ESCALATE** requires $P(H_4) \ge 0.70$ **AND** at least 2 independent verified reporting sources.

9. **Persistence (`app/database/database.py`)**:
   - Local SQLite database (`data/crisispulse.db`) with Write-Ahead Logging (WAL) and indexed lookups.
   - Persists events, source health history, hypothesis trajectories, forecasts, decisions, evaluations, and audit ledgers.

10. **First-10-Minute Intelligence Lab (`app/intelligence_lab/lab.py`)**:
    - Minute-by-minute historical evidence replay.
    - Side-by-side Twin Test disambiguating disasters from hardware telemetry failures.
    - Counterfactual "What-If" analysis.
    - Traceable evidence provenance.
