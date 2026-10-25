# CrisisPulse AI · Developer Handoff & Operations Manual
**Nagpur Live Emergency Intelligence Platform · The First 10 Minutes**

---

## 1. System Overview

CrisisPulse AI is an operational early-warning intelligence platform designed for municipal disaster managers, emergency controllers, and response commanders during the critical **First 10 Minutes** of emerging cascading disasters.

The system combines multi-source environmental telemetry, municipal drainage sensors, traffic congestion feeds, and hospital surge metrics across Nagpur District and the 10 administrative zones of the Nagpur Municipal Corporation (NMC). It maintains continuous Bayesian belief distributions across four competing operational hypotheses, minimizes expected cost under uncertainty, stabilizes alerts with hysteresis, projects multi-horizon causal forecasts, and generates evidence-grounded natural-language explanations.

### Key Architectural Upgrades in this Release:
1. **Four Hypotheses Core**: `noise` ($H_1$), `sensor_failure` ($H_2$), `isolated_incident` ($H_3$), `cascading_crisis` ($H_4$) with mathematical guarantee $\sum P(H_i) = 1.00$.
2. **The Twin Test Benchmark**: Formal verification that minutes 0 through 6 share identical timestamps, source IDs, evidence ordering, probabilities, and actions before diverging at minute 7.
3. **Online Bayesian Trust Learning**: Conjugate $\text{Beta}(\alpha, \beta)$ distributions per source, category vectors, and tracking of correlated gateway groups.
4. **Environmental Base-Rate Adaptation**: Dirichlet-style seasonal prior shifting between monsoon and non-monsoon periods.
5. **Alert Stability & Dual-Threshold Hysteresis**: Escalation enter $\ge 0.70$, exit $< 0.50$, persistence requirements, 180s cooldown, and zero-latency emergency overrides.
6. **Messy Stream Management**: Idempotent event fingerprinting, event retractions (`retraction`), and superseding correction tracking.
7. **Predictive Multi-Horizon Forecasting**: 3 distinct projections (10, 30, 60 min) with strict temporal DAG precedence and hydrodynamic lag constraints.
8. **TantraFiesta UI Redesign**: Indian Maximalist visual language inspired by `https://www.tantrafiesta.in/` (aubergine, saffron, royal fuchsia, cyan telemetry, warm ivory typography).

---

## 2. Quickstart Runbook

### Prerequisites
- Python 3.10+ (Verified on Python 3.14)
- Node.js 18+ (Verified on Node.js v24)
- npm or pnpm

### Step 1: Environment Setup
```bash
cp .env.example .env
```
*(No third-party API keys are required to run locally; transparent fallback reference data is included for all feeds).*

### Step 2: Start Backend (FastAPI + Uvicorn)
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base: `http://127.0.0.1:8000`
- Interactive Swagger: `http://127.0.0.1:8000/docs`
- WebSocket: `ws://127.0.0.1:8000/ws`

### Step 3: Start Frontend (Vite + React)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 3. Running Automated Tests & Verification

### Backend Tests
```bash
python -m pytest backend/tests/test_challenge_alignment.py backend/tests/test_lab_and_evaluation.py backend/tests/test_engine.py backend/tests/test_inference_and_decisions.py backend/tests/test_pipeline.py backend/tests/test_geography.py backend/tests/test_xai.py -v
```
All 30 unit and integration tests pass cleanly in ~1.0 second.

### Frontend Production Build
```bash
npm --prefix frontend run build
```
Compiles TypeScript with 0 errors and generates production bundles.

---

## 4. Key Endpoints Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/state` | GET | Full operational state snapshot with probabilities and action |
| `/api/twin-test` | GET | Runs Twin Test benchmark with prefix verification and avoided costs |
| `/api/lab/replay` | GET | Scrubber replay sequence across all 16 scenarios |
| `/api/lab/counterfactual` | POST | Evaluates counterfactual what-if scenarios |
| `/api/learning/experiment` | POST | Triggers ground-truth verification and Beta trust update |
| `/api/base-rate/drift` | GET | Current Dirichlet environmental base-rate drift state |
| `/api/base-rate/adapt` | POST | Manually shifts base-rate priors (e.g. monsoon season) |
| `/api/retractions/audit` | GET | Complete audit trail of retracted and superseded events |
| `/api/region/{zone_id}` | GET | Zone-specific risk and evidence assessment |
| `/api/xai/explain` | POST | Generates evidence-grounded natural language explanation |
| `/ws` | WebSocket | Real-time push updates for live events and state changes |

---

## 5. Non-Autonomy & Safety Principle

CrisisPulse AI is strictly an **advisory decision-support platform**:
- It **does not** autonomously dispatch municipal response teams or field equipment.
- It **does not** broadcast unverified evacuation orders to the public.
- All high-impact tactical decisions require human commander authorization.
