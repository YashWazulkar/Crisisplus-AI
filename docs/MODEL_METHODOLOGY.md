# CrisisPulse AI 2.0 — Model Methodology & Theoretical Formulation
**Continuous Online Bayesian Inference, Expected-Cost Decision Optimization & Causal Forecasting**

---

## 1. Probabilistic Formulation & The Four Hypotheses

CrisisPulse AI rejects black-box neural heuristics for emergency early warning, prioritizing **statistically defensible, calibrated Bayesian inference** combined with robust anomaly detection, cost-aware decision theory, and causal graph propagation.

### 1.1 The Four Mutually Exclusive Hypotheses

At any time tick $t$, the system maintains a complete probability distribution over four mutually exclusive operational hypotheses:

$$\sum_{i=1}^4 P(H_i \mid \mathcal{E}_{1:t}) = 1.0$$

1. **$H_1$ — Normal Conditions / Noise (`noise` / `normal`)**: Environmental parameters and traffic telemetry reflect expected diurnal patterns or benign sensor fluctuations without threatening public safety.
2. **$H_2$ — Data-Source / Sensor Failure (`sensor_failure` / `source_failure`)**: Extreme readings or missing reports are attributable to hardware faults, gateway lockups, transmission timeouts, corrupted telemetry, or uncalibrated sensors.
3. **$H_3$ — Isolated Incident (`isolated_incident`)**: A real localized incident has occurred (e.g., single-vehicle collision, small trash fire, localized minor intersection puddle), but systemic cascading risk across municipal infrastructure is absent.
4. **$H_4$ — Cascading Emergency Crisis (`cascading_crisis`)**: Compound multi-sector disaster propagation (e.g., torrential cloudburst inundating drainage networks, causing arterial gridlock that delays emergency response vehicles and overwhelms hospital critical care facilities).

Every system assessment guarantees:
- $0 \le P(H_i) \le 1.0$ for all $i \in \{1, 2, 3, 4\}$.
- $\sum_{i=1}^4 P(H_i) = 1.0$ within floating-point tolerance ($10^{-9}$).
- Missing evidence does not automatically inflate crisis posterior.
- Common-cause source outages do not count as independent proof of disaster.

---

## 2. Tempered Bayesian Belief Updating

Incoming observations undergo tempered Bayesian updating to account for data quality, freshness decay, and uncorroborated rumors:

$$P(H_i \mid E) = \frac{P(H_i) \cdot \left[ P(E \mid H_i) \right]^\omega}{\sum_{j=1}^4 P(H_j) \cdot \left[ P(E \mid H_j) \right]^\omega}$$

Where $\omega \in [0.05, 1.0]$ represents the composite evidence quality weight:

$$\omega = \text{Trust}(\text{Source}) \cdot \left( 0.6 \cdot e^{-\lambda \Delta t} + 0.4 \cdot \text{Completeness} \right) \cdot \prod_{k} \text{Penalty}_k$$

- **Freshness Decay**: $\lambda = \frac{\ln(2)}{t_{1/2}}$ with half-life $t_{1/2} = 2.0\text{ hours}$.
- **Unverified Reports**: $\text{Penalty} = 0.50$.
- **Shared Gateway Infrastructure**: $\text{Penalty} = 0.85$ (discounts co-located sensors sharing one gateway controller).
- **Correlated Social Reports**: $\text{Penalty} = 0.65$.
- **Hypothesis Transition Floor**: An explicit floor $\epsilon = 0.035$ prevents hypothesis starvation or permanent zero-probability lock, allowing the system to recognize sensor failures even after an initial surge.

---

## 3. Online Trust Learning: Beta Conjugate Updating

Rather than assuming static source reliability, the system maintains a Bayesian conjugate model for each data source's reporting veracity:

$$\text{Trust}(s) \sim \text{Beta}(\alpha_s, \beta_s)$$

- **Prior Distribution**: Initialized with uninformative or historical priors (e.g., $\alpha_0 = 9.5, \beta_0 = 1.5$ for calibrated telemetry; $\alpha_0 = 5.0, \beta_0 = 5.0$ for crowd reports).
- **Online Posterior Update**: Upon arrival of verified ground-truth outcome $y \in [0, 1]$:
  $$\alpha_s \leftarrow \alpha_s + \eta \cdot y$$
  $$\beta_s \leftarrow \beta_s + \eta \cdot (1 - y)$$
  Where $\eta \in (0, 1]$ is the verification learning rate.
- **Expected Trust & Uncertainty**:
  $$\mathbb{E}[\text{Trust}(s)] = \frac{\alpha_s}{\alpha_s + \beta_s}$$
  $$\text{Var}[\text{Trust}(s)] = \frac{\alpha_s \beta_s}{(\alpha_s + \beta_s)^2 (\alpha_s + \beta_s + 1)}$$

High variance sources automatically receive lower tempered evidence weights ($\omega$) until verified by corroborating channels.

---

## 4. Environmental Base-Rate Adaptation

Prior probabilities $P(H_i)$ are not treated as immutable constants. During active monsoon periods or environmental drift, the base probability of drainage surcharges and flash flooding naturally rises:

$$P_{\text{adapted}}(H_i) = (1 - \gamma) \cdot P_{\text{prior}}(H_i) + \gamma \cdot P_{\text{environmental}}(H_i)$$

- **Dirichlet Smoothing**: Bounded adaptation ensures prior probabilities stay strictly within operational bounds:
  $$P_{\text{min}} \le P(H_i) \le P_{\text{max}}$$
  $$\sum_{i=1}^4 P_{\text{adapted}}(H_i) = 1.0$$
- This prevents out-of-season false alarms during dry months while ensuring high sensitivity during monsoon warnings.

---

## 5. Expected-Cost Decision Theory & Alert Stability

Operational action selection is formulated under formal decision theory across four discrete strategies: $\mathcal{A} = \{\text{WATCH}, \text{PREPARE}, \text{ALERT}, \text{ESCALATE}\}$.

### 5.1 Asymmetric Loss Matrix $L(A, H_i)$

$$\mathbb{E}[\text{Loss}(A)] = \sum_{i=1}^4 P(H_i) \cdot L(A, H_i)$$

| Response Action | $H_1$ (Normal) | $H_2$ (Failure) | $H_3$ (Isolated) | $H_4$ (Cascade) |
| :--- | :---: | :---: | :---: | :---: |
| **WATCH** | 0.0 | 1.2 | 7.5 | 18.0 |
| **PREPARE** | 2.2 | 2.0 | 3.8 | 8.0 |
| **ALERT** | 6.5 | 5.0 | 2.0 | 3.0 |
| **ESCALATE** | 13.0 | 10.5 | 5.2 | 1.0 |

The optimal unconstrained action is:
$$A^* = \arg\min_{A \in \mathcal{A}} \mathbb{E}[\text{Loss}(A)]$$

### 5.2 Multi-Source Corroboration Gating

Autonomous false alarms carry severe civic and economic costs. Action **ESCALATE** requires:
1. $P(H_4) \ge 0.70$
2. Corroboration from at least **2 distinct, independent, unflagged data sources** (e.g. Open-Meteo precipitation gauge corroborated by municipal water level sensor or traffic police field confirmation).
3. If only one source reports the hazard, the recommendation is gated to **ALERT**, requesting field verification.

### 5.3 Alert Stability & Dual-Threshold Hysteresis

To prevent high-frequency alert thrashing near decision boundaries:
- **Dual-Threshold Trigger**:
  - Enter **ESCALATE**: $P(H_4) \ge 0.70$
  - Exit **ESCALATE**: $P(H_4) < 0.50$
- **Persistence Counter**: Requires $k \ge 2$ consecutive ticks in the higher state before escalating.
- **Cooldown Interval**: Minimum 180 seconds between non-emergency downgrades.
- **Emergency Override**: Rapid compound shocks ($P(H_4) \ge 0.90$ with multiple verified sources) bypass cooldown instantly.

---

## 6. The Twin Test: Disambiguation Benchmark

The central benchmark in the First 10 Minutes Intelligence Lab tests whether the model can distinguish a genuine escalating crisis from a hardware telemetry failure when both share identical initial conditions.

### 6.1 Identical Prefix (Minutes 0–6)
- **Twin A** and **Twin B** receive **strictly identical evidence**:
  - Identical event IDs (`twin-shared-{seed}-m{minute}`).
  - Identical timestamps, source IDs, geographic coordinates, and order of arrival.
  - Ambiguous weather and drainage telemetry: Rainfall 22–32 mm/h, water stage 0.9–1.2m.
- **Mathematical Equality Requirement**:
  $$\forall m \in \{0, \dots, 6\}, \quad |P_A(H_i)_m - P_B(H_i)_m| < 10^{-4}$$
  $$\text{Action}_A(m) \equiv \text{Action}_B(m) \in \{\text{WATCH}, \text{PREPARE}\}$$
  The model has zero knowledge of future events or ground-truth scenario labels.

### 6.2 Divergence at Minute 7
- **Twin A (Genuine Cascade)**: Independent traffic police confirm arterial road submersion (severity 0.91, physical ground verification). Multi-source corroboration triggers **ALERT** then **ESCALATE** ($P(H_4) \to 0.97$).
- **Twin B (Sensor Look-alike)**: Drainage sensor gateway controller times out with hardware error (severity 0.96). The model identifies common-cause failure, discounts anomalous water readings, and stabilizes at **PREPARE/WATCH** ($P(H_2) \to 0.93$).

### 6.3 Benchmark Metrics Exposed
1. **Divergence Minute**: Exactly minute 7.
2. **Time to Justified Detection**: Minute 7 (immediate response upon corroborated evidence arrival).
3. **Premature Confidence Penalty**: $0.00$ (zero premature escalation during ambiguous minutes 0–6).
4. **False-Alarm Cost Avoided**: $+\$9.30$ (calculated via expected loss delta in Twin B).
5. **Missed-Detection Cost Avoided**: $+\$17.00$ (calculated via expected loss delta in Twin A).

---

## 7. Real-Time Messy Event Stream Processing

The ingestion pipeline handles messy asynchronous real-world streams via defensive stream primitives:

### 7.1 Idempotency & Deduplication
- Content-addressable event fingerprinting based on:
  $$\text{Hash}(\text{source\_id}, \text{event\_type}, \text{zone\_id}, \text{rounded\_time}_{3\text{min}})$$
- Repeated ingestion of duplicate packets is recognized and discarded without repeatedly compounding the Bayesian likelihood.

### 7.2 Retractions and Superseding Corrections
- Retracted events (e.g., citizen rumors contradicted by official police verification) are flagged as `retraction`.
- The `EventRetractionManager` marks retracted events, zeroing their positive evidence contribution in subsequent Bayesian updates.
- Corrected observations supersede earlier versions via `superseded_by` links, maintaining a full audit ledger.

### 7.3 Bounded Out-of-Order Reassembly
- Events arriving late (within a 10-minute historical buffer) are sorted by event occurrence time rather than ingestion receipt time, recomputing affected state transitions deterministically.

---

## 8. Multi-Horizon Causal Forecasting & DAG Latency Constraints

The system projects the next three plausible disaster events at +10, +30, and +60 minutes.

### 8.1 Temporal Precedence & Physical Propagation Latency
In the causal directed acyclic graph (DAG), an edge $A \to B$ is active if and only if:
1. $t_A < t_B$ (strict temporal precedence).
2. $\Delta t = t_B - t_A \in [\tau_{\text{min}}, \tau_{\text{max}}]$ (respecting physical propagation lag, e.g., 3 to 30 minutes for surface runoff to reach downstream channels).
3. Spatial co-location: Zone $A$ matches Zone $B$ or drains directly into Zone $B$.

Temporal reversal correlations ($t_B \le t_A$) are strictly rejected by the causal graph.

### 8.2 Forecast Object Schema
Each forecast explicitly exposes:
- `event_type`: Specific hazard event projected.
- `label`: Natural language description.
- `horizon`: Projected time horizon (e.g. "+10 to +25 min").
- `time_window_minutes`: Explicit bounds `[start_min, end_min]`.
- `window_start_iso` / `window_end_iso`: ISO 8601 operational time windows.
- `probability`: Calibrated likelihood $[0, 1]$.
- `confidence_band`: Confidence classification (`HIGH`, `MODERATE`, `LOW`).
- `causal_chain`: Ordered array of upstream events leading to this projection.
- `evidence_basis`: Specific telemetry observations grounding the forecast.
- `uncertainty_alternative`: Alternative physical branch if conditions diverge.
- `data_basis`: Methodological basis (`OBSERVED_DATA + CAUSAL_RULE`, `STATISTICAL_MODEL`).
- `assumptions` & `known_limitations`: Explicit disclosures of model constraints.

---

## 9. Explainable AI (xAI) & Grounding Protection

Natural-language summaries are produced through an evidence-grounded layer (compatible with xAI Grok and deterministic fallbacks).

- **The Grounding Protection Rule**: An LLM cannot override, modify, or escalate the authoritative response action or mathematical probabilities produced by the Bayesian/Decision engine.
- Every explanation outputs:
  - Decision rationale matching the authoritative action.
  - Field evidence synthesis linking observations to sources.
  - Contradictory evidence and discrepancy disclosures.
  - Explicit missing data disclosures.
  - Step-by-step verification checklist for field response commanders.
