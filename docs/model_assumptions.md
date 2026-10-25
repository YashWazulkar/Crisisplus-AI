# CrisisPulse AI · Mathematical Methodology & Model Assumptions

This document outlines the mathematical foundation, probabilistic assumptions, and operational constraints governing the CrisisPulse AI inference engine and decision framework for Nagpur.

---

## 1. Probabilistic Formulation & Hypothesis Space

CrisisPulse AI rejects uncalibrated black-box classification in favor of **calibrated Bayesian belief tracking** over four mutually exclusive and exhaustive operational hypotheses:

$$\sum_{i=1}^4 P(H_i \mid \mathcal{E}_{1:t}) = 1.0$$

1. **$H_1$ — Normal Baseline Conditions**: Environmental, weather, and transit metrics fluctuate within customary seasonal and diurnal envelopes.
2. **$H_2$ — Data-Source or Sensor Failure**: Extreme signals or abrupt dropouts arise from telemetry failure, hardware lockups, dead batteries, network timeouts, or uncalibrated sensors.
3. **$H_3$ — Isolated Incident**: A verified, real-world incident is occurring (e.g. localized traffic collision, tree branch blocking a street, isolated vehicle fire), but impacts remain localized without cross-sector infrastructure cascading.
4. **$H_4$ — Potential Cascading Crisis**: A severe, multi-domain hazard event (e.g. torrential cloudburst overwhelming municipal culverts, causing arterial roadway flooding, blocking ambulance transit corridors to GMCH Trauma Center, and surging emergency room demand).

### Baseline Priors
When initialized or reset, the system starts with conservative empirical priors:
- $P(H_1) = 0.550$
- $P(H_2) = 0.150$
- $P(H_3) = 0.200$
- $P(H_4) = 0.100$

A minimum probability floor $\epsilon = 0.035$ prevents hypothesis starvation or irreversible posterior saturation.

---

## 2. Tempered Bayesian Belief Updating

Incoming normalized observations $E$ update the belief distribution via tempered Bayesian conditioning:

$$P(H_i \mid E) = \frac{P(H_i) \cdot \left[ P(E \mid H_i) \right]^\omega}{\sum_{j=1}^4 P(H_j) \cdot \left[ P(E \mid H_j) \right]^\omega}$$

Where $\omega \in [0.05, 1.0]$ represents the composite evidence quality weight:

$$\omega = \text{Reliability}(S) \cdot \left( 0.6 \cdot e^{-\lambda \Delta t} + 0.4 \cdot \text{Completeness} \right) \cdot \prod_{k} \text{Penalty}_k$$

### Freshness Decay
Observation weight decays exponentially as temporal age $\Delta t$ increases:

$$\text{Decay}(\Delta t) = \exp\left( -\frac{\ln(2)}{t_{1/2}} \cdot \Delta t \right)$$

Where $t_{1/2} = 2.0\text{ hours}$ for meteorological and drainage sensors.

### Quality Penalties
- **Unverified Field Report**: $\text{Penalty} = 0.50$
- **Correlated / Shared Gateway Infrastructure**: $\text{Penalty} = 0.85$ (mitigates common-mode failure overconfidence)
- **High Ingestion Latency ($> 15\text{ min}$)**: $\text{Penalty} = 0.70$
- **Low Confidence ($< 0.50$)**: $\text{Penalty} = 0.60$

---

## 3. Anomaly Detection & Swarm Clustering

### Median Absolute Deviation (MAD) Robust Z-Scores
Because environmental sensors frequently produce extreme spikes that distort classical sample means and standard deviations, the anomaly detector computes robust Z-scores using the median and MAD:

$$\text{MAD} = \text{median}\left( |x_i - \text{median}(X)| \right)$$
$$\text{Robust } Z = \frac{x_t - \text{median}(X)}{1.4826 \times \text{MAD}}$$

An anomaly flag `precipitation_burst` is registered when $\text{Robust } Z \ge 3.0$ and absolute rate $x_t \ge 15.0\text{ mm/h}$.

### Spatial Concentration Swarms
Using the Haversine spherical distance function, the engine detects hazard spatial clustering:

$$d = 2R \arcsin \left( \sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)} \right)$$

If $\ge 3$ distinct incidents are detected within a 35 km radius within 30 minutes, a `spatial_cluster_swarm` anomaly is flagged.

---

## 4. Expected-Cost Decision Optimization & Cautious Escalation

### Action Space
The platform evaluates four operational posture actions:
- **`WATCH`**: Passive monitoring and routine health pinging.
- **`PREPARE`**: Advisory staging; verify backup generators, alert standby pump crews.
- **`ALERT`**: Tactical mobilization; position high-capacity dewatering pumps, deploy traffic police to underpasses.
- **`ESCALATE`**: Strategic emergency mobilization; open municipal emergency operations center, activate multi-agency crisis coordination.

### Prototype Cost Matrix $C(a, H_i)$
The loss associated with taking action $a$ when ground truth state is $H_i$:

| Action $a$ | $H_1$ (Normal) | $H_2$ (Sensor Failure) | $H_3$ (Isolated) | $H_4$ (Cascade) |
| :--- | :---: | :---: | :---: | :---: |
| **WATCH** | $0.00$ | $0.05$ | $0.35$ | $1.00$ |
| **PREPARE**| $0.10$ | $0.15$ | $0.15$ | $0.50$ |
| **ALERT** | $0.30$ | $0.40$ | $0.10$ | $0.20$ |
| **ESCALATE**| $0.70$ | $0.85$ | $0.30$ | $0.05$ |

The expected loss for each candidate action is:

$$\mathbb{E}[L(a)] = \sum_{i=1}^4 P(H_i) \cdot C(a, H_i)$$

The optimal candidate action minimizes expected loss:

$$a^* = \arg\min_a \mathbb{E}[L(a)]$$

### Cautious Escalation Gates & Anti-Hysteresis
To prevent false alarms driven by single-sensor malfunctions:
1. **Probability Gate**: $a^* = \text{ESCALATE}$ is permitted only if $P(H_4) \ge 0.70$.
2. **Corroboration Gate**: Must be corroborated by $\ge 2$ independent data sources with reliability $\ge 0.60$.
3. **Hysteresis Deadband**: De-escalating from `ESCALATE` to `ALERT` requires $P(H_4)$ to drop below $0.55$ for at least 3 consecutive evaluation cycles, preventing rapid state oscillation.

---

## 5. Multi-Horizon Forecast Projections

Near-term projections are generated across three discrete operational horizons:
- **$T+10\text{ min}$ (Immediate Physical State)**: Models localized culvert filling, underpass ponding rate, and road closure inception.
- **$T+30\text{ min}$ (Arterial Transit & Propagation)**: Models traffic queue propagation along Wardha Road, Central Avenue, and ambulance transit latency to GMCH.
- **$T+60\text{ min}$ (Institutional Surge & Capacity)**: Models emergency department triage queues and inpatient surge at Level 1 trauma facilities.

Projections are conditioned on both numerical weather prediction inputs and the current posterior $P(H_4)$.

---

## 6. Grounded Explainability (xAI) Boundaries

CrisisPulse AI integrates xAI Grok strictly as a **grounded natural language synthesiser**, never as an autonomous decision-maker:
- **Input Constraint:** Grok receives an immutable `EvidencePacket` containing pre-computed Bayesian probabilities, dominant hypotheses, active sensor readings, and geographic precision levels.
- **Grounding Invariant:** The output is validated by `XAIGroundingValidator`. If Grok generates an action that disagrees with the mathematical engine or cites non-existent sensors, the system automatically falls back to deterministic rule-based synthesis.
- **Non-Autonomy Invariant:** The system produces human decision support only. It is strictly prohibited from autonomously triggering public evacuation sirens or dispatching emergency units.
