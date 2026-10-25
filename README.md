# CrisisPulse AI · Nagpur Live Emergency Intelligence Platform
**Continuous Online Bayesian Early-Warning System for "The First 10 Minutes" of Cascading Disasters**

> **Real-time, evidence-grounded emergency intelligence, multihazard early warning, and decision support for Nagpur District and the Nagpur Municipal Corporation (NMC).**
> Inspired by [TantraFiesta](https://www.tantrafiesta.in/) — blending Indian Maximalist command-center aesthetics with calibrated decision theory.

---

## 1. Key Capabilities & System Innovations

CrisisPulse AI addresses the core emergency challenge: **a disaster rarely begins at the moment it becomes visible.** Between minute 0 and minute 10, duty officers face ambiguous, messy, asynchronous, and corruptible streams. The platform infers the hidden state, avoids premature panic, and takes cost-optimal actions under uncertainty.

### Core Mathematical & Operational Innovations:
1. **Four Competing Mutually Exclusive Hypotheses**:
   - `noise` / `normal`: Ordinary environmental variation or uncalibrated fluctuations ($H_1$).
   - `sensor_failure` / `source_failure`: Corrupted telemetry, hardware fault, or common-cause gateway outage ($H_2$).
   - `isolated_incident`: Genuine localized incident without systemic infrastructure cascade ($H_3$).
   - `cascading_crisis`: Compound multi-sector emergency cascading across drainage, power, transport, and hospitals ($H_4$).
   - Guaranteed $\sum_{i=1}^4 P(H_i) = 1.00$ with Dirichlet prior adaptation and hypothesis starvation prevention.
2. **The Twin Test Disambiguation Benchmark**:
   - Twin A (genuine cascade) and Twin B (gateway hardware glitch) share an **identical event history from minute 0 through minute 6**.
   - Formally asserted: identical timestamps, source IDs, evidence ordering, probabilities, and actions in minutes 0–6.
   - At minute 7, Twin A receives independent ground confirmation (escalating to ALERT/ESCALATE), while Twin B isolates a gateway controller failure (stabilizing at PREPARE/WATCH).
   - Exposes divergence minute (7), time to justified detection (T+7m), premature confidence penalty (0.00), false-alarm cost avoided (+$9.30), and missed-detection cost avoided (+$17.00).
3. **16 Standardized Operational Scenarios**:
   - Standardized adversarial library in `backend/app/simulator.py` covering rapid flash floods, correlated gateway outages, rumor retractions, delayed arrivals, duplicate bursts, and environmental base-rate drift.
4. **Online Trust Learning & Source Health**:
   - Conjugate $\text{Beta}(\alpha, \beta)$ online reliability tracking per provider and gateway group.
   - Learns from verified ground-truth outcomes, tracking parameter variance and preventing correlated failure counting.
5. **Alert Stability & Dual-Threshold Hysteresis**:
   - Eliminates alert thrashing near decision boundaries: enter ESCALATE at $P(H_4) \ge 0.70$, exit only when $P(H_4) < 0.50$.
   - Enforces $k \ge 2$ persistence ticks, a 180s cooldown, and mandatory 2-source corroboration before escalation.
6. **Multi-Horizon Causal Forecasting**:
   - Projects three distinct causal events at 10, 30, and 60 minutes.
   - Grounded in strict causal DAG rules enforcing temporal precedence ($t_{\text{src}} < t_{\text{dst}}$) and hydrodynamic lag windows.
7. **TantraFiesta Indian Maximalism UI Redesign**:
   - Deep aubergine/midnight void base (`#09040e`), glowing saffron/amber hairlines (`#f59e0b`), royal fuchsia badges (`#d946ef`), vivid cyan telemetry (`#06b6d4`), and high-contrast warm ivory typography (`#fdfcf7`, 16.5:1 contrast ratio).
   - Redesigned 4-tab Intelligence Lab: Minute-by-Minute Replay, Twin Test Benchmark, What-If Counterfactuals, and Online Trust & Health.

---

## 2. Operational Architecture

```
                    EXTERNAL DATA FEEDS (NAGPUR REGION)
  [IMD Nagpur]  [Open-Meteo]  [NMC Drainage]  [Hospitals]  [Traffic]  [FIRMS]  [USGS]  [GDACS]
         │            │              │              │          │        │        │        │
         └────────────┴──────────────┼──────────────┴──────────┴────────┴────────┴────────┘
                                     ▼
                   MESSY STREAM INGESTION & QUALITY PIPELINE
               - Deduplication & Idempotent Fingerprinting (Hash)
               - Retraction & Correction Manager (Superseded Tracking)
               - Bounded 10-Min Out-of-Order Reassembly
               - Common-Cause Gateway Group Tracking
                                     ▼
                  ONLINE LEARNING & BASE-RATE ADAPTATION
               - Beta(α, β) Bayesian Conjugate Source Veracity
               - Dirichlet Monsoon Environmental Drift Tracking
                                     ▼
                       PROBABILISTIC INFERENCE ENGINE
               - 4 Hypotheses: Noise (H1), Failure (H2), Isolated (H3), Cascade (H4)
               - Tempered Bayesian Posterior: P(Hi | E) ∝ P(Hi) · P(E | Hi)^ω
               - Anomaly Detection: Robust Median Absolute Deviation (MAD Z-Scores)
                                     ▼
                   EXPECTED-COST DECISION & STABILITY POLICY
               - Asymmetric Loss Minimization across WATCH, PREPARE, ALERT, ESCALATE
               - Dual-Threshold Hysteresis (Enter ≥0.70, Exit <0.50)
               - 2-Source Corroboration Gating & Cooldown Timers
                                     ▼
                     CAUSAL GRAPH & MULTI-HORIZON FORECASTS
               - Temporal Precedence (t_src < t_dst) & Hydrologic Latency Windows
               - Forecast Horizons: T+10m (Underpass), T+30m (Transit), T+60m (Trauma Intake)
                                     ▼
                   TANTRAFIESTA INDIAN MAXIMALIST COMMAND CENTER
               - Operational Header, Real-Time WebSocket, & NMC 10-Zone GeoJSON Map
               - 4-Tab First-10-Minutes Intelligence Lab (Twin Test, Counterfactuals)
               - Explainable AI (xAI Grok / Deterministic) with Grounding Protection
```

---

## 3. Quickstart Guide

### 3.1 Prerequisites
- Python 3.10+ (Verified on Python 3.14)
- Node.js 18+ (Verified on Node.js v24)
- npm / pnpm

### 3.2 Backend Setup
```bash
# Configure environment variables (optional: add XAI_API_KEY, IMD_API_KEY)
cp .env.example .env

# Run FastAPI backend with Uvicorn
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base: `http://127.0.0.1:8000`
- Interactive API Docs: `http://127.0.0.1:8000/docs`
- WebSocket Stream: `ws://127.0.0.1:8000/ws`

### 3.3 Frontend Setup
In a separate terminal:
```bash
cd frontend

# Install dependencies and launch Vite development server
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 4. Running Automated Tests & Verification

### Backend Automated Test Suite
Run the test suites:
```bash
python -m pytest backend/tests/test_challenge_alignment.py backend/tests/test_lab_and_evaluation.py backend/tests/test_engine.py backend/tests/test_inference_and_decisions.py backend/tests/test_pipeline.py backend/tests/test_geography.py backend/tests/test_xai.py -v
```
All 30 unit and integration tests verify:
- Four-hypothesis mathematical invariants ($\sum P = 1.00$).
- The Twin Test identical prefix verification (min 0–6) and minute 7 divergence.
- Event retraction and superseding correction deduplication.
- Online Beta trust updating and environmental base-rate adaptation.
- Alert stability hysteresis and 2-source corroboration gating.
- Causal graph temporal ordering and latency constraints.
- xAI grounding protection ensuring deterministic overrides cannot be bypassed.

### Frontend TypeScript & Asset Build
```bash
npm --prefix frontend run build
```
Compiles TypeScript with zero errors into production-ready optimized bundles.

---

## 5. Documentation Suite

Detailed architectural, operational, and mathematical documentation is available in `docs/`:

- [**UI Design System (TantraFiesta)**](docs/ui_design_system.md): Color tokens, typography, Indian Maximalist accents, layout grid, and accessibility standards.
- [**Model Methodology & Theoretical Formulation**](docs/MODEL_METHODOLOGY.md): Mathematical formulations for Bayesian inference, Beta trust updating, Dirichlet adaptation, decision matrices, and forecasting equations.
- [**Remaining Work Audit**](docs/remaining_work_audit.md): Complete requirements audit and verification evidence matrix.
- [**Data Sources & Connectors**](docs/data_sources.md): Specifications, endpoints, authentication, and fallback behaviors for all 8 feeds.
- [**Geographic Data**](docs/geographic_data.md): Nagpur district boundaries, 10 NMC administrative zones, 7 chronic hotspots, 6 trauma hospitals, and 3 river corridors.
- [**Developer Handoff**](HANDOFF.md): Operations manual, runbooks, and production roadmap.

---

## 6. Safety & Human-in-the-Loop Disclaimer

CrisisPulse AI is designed exclusively as an operational decision-support tool for municipal emergency directors and incident commanders.
- It **does not** automatically dispatch emergency response units.
- It **does not** autonomously issue public emergency or evacuation alerts.
- All high-impact tactical actions remain subject to human review and authorized protocol execution.
