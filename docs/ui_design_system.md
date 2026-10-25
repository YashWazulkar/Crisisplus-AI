# CrisisPulse AI · TantraFiesta UI Design System
**Indian Maximalism × Contemporary Futuristic Command Center × Disaster Decision Intelligence**

---

## 1. Executive Vision & Design Philosophy

CrisisPulse AI's operational user interface is directly inspired by the design language of **[TantraFiesta](https://www.tantrafiesta.in/)** — fusing rich Indian Maximalist cultural aesthetics with a high-performance, futuristic command center.

In disaster operations, visual clarity, spatial hierarchy, and rapid cognitive ingestion can save lives. The interface abandons sterile enterprise gray dashboards in favor of:
- **Atmospheric Depth:** Deep aubergine, void black, and midnight violet base canvases evoke the drama and gravity of emergency response.
- **Cultural Maximalism:** Gold/saffron borders, delicate glowing hairlines, and royal fuchsia accents celebrate festive tech maximalism without compromising operational discipline.
- **Strict Semantic Integrity:** Standard emergency severity colors (Green for WATCH, Yellow for PREPARE, Amber for ALERT, Crimson for ESCALATE) are rigorously preserved to ensure immediate, zero-ambiguity cognitive parsing by duty officers and incident commanders.

---

## 2. Color Palette & Token Architecture

All tokens are defined in CSS custom properties inside `frontend/src/style.css`.

### 2.1 Core Foundations (The Midnight Canvas)
| Token | Hex Value | Role & Usage |
|---|---|---|
| `--bg-void` | `#09040e` | Deepest root background with radial atmospheric gradients |
| `--bg-primary` | `#0d0714` | Primary viewport background and header container |
| `--bg-secondary` | `#130a1e` | Secondary utility panels, toolbars, and search containers |
| `--bg-tertiary` | `#1b0e2b` | Inset code blocks, progress track wells, and metadata badges |
| `--bg-card` | `#160c25` | Standard card surface |
| `--bg-card-elevated` | `#201036` | Active, hover, and prominent decision panels |
| `--bg-glass` | `rgba(22, 12, 37, 0.82)` | Frosted glass modals and floating inspector headers |

### 2.2 Indian Maximalist Accents
| Token | Hex Value | Role & Usage |
|---|---|---|
| `--saffron-500` | `#f59e0b` | Sacred saffron; primary action buttons, active tab borders, highlights |
| `--saffron-400` | `#fbbf24` | Warm gold; telemetry highlights, key probabilities, focus outlines |
| `--saffron-glow` | `rgba(245, 158, 11, 0.22)` | Subtle radial glow around active operational cards |
| `--fuchsia-500` | `#d946ef` | Royal fuchsia; AI/ML inference badges, verified intelligence tags |
| `--fuchsia-400` | `#e879f9` | Bright fuchsia; secondary accents and subagent telemetry |
| `--violet-700` | `#4c1d95` | Deep royal violet; card drop shadows and divider lines |
| `--violet-400` | `#a78bfa` | Sensor failure hypothesis tag, secondary data quality signals |
| `--marigold` | `#f97316` | Marigold alert; intermediate warning highlights |

### 2.3 Typography & Contrast Hierarchy
| Token | Hex Value | Role & Usage |
|---|---|---|
| `--text-ivory` | `#fdfcf7` | High-contrast warm ivory; primary headlines and metrics (WCAG AAA: 16.5:1) |
| `--text-primary` | `#f4efe4` | Card titles, body copy, and decision rationales |
| `--text-secondary` | `#c7beaf` | Metadata labels, descriptions, and secondary details |
| `--text-muted` | `#8e8299` | Timestamps, table column headers, and inactive states |
| `--text-dim` | `#5d506d` | Disclaimers, caveats, and baseline indicators |

### 2.4 Telemetry & Operational Postures
| Posture / State | Primary Color | Background Tint | Border Accent |
|---|---|---|---|
| **WATCH** | `#10b981` (Emerald) | `rgba(16, 185, 129, 0.12)` | `rgba(16, 185, 129, 0.35)` |
| **PREPARE** | `#eab308` (Saffron Yellow) | `rgba(234, 179, 8, 0.12)` | `rgba(234, 179, 8, 0.40)` |
| **ALERT** | `#f97316` (Marigold Amber) | `rgba(249, 115, 22, 0.14)` | `rgba(249, 115, 22, 0.45)` |
| **ESCALATE** | `#ef4444` (Crimson Red) | `rgba(239, 68, 68, 0.16)` | `rgba(239, 68, 68, 0.55)` |
| **SENSOR FAILURE** | `#a855f7` (Royal Violet) | `rgba(168, 85, 247, 0.12)` | `rgba(168, 85, 247, 0.40)` |
| **CYAN TELEMETRY** | `#06b6d4` (Electric Cyan) | `rgba(6, 182, 212, 0.12)` | `rgba(6, 182, 212, 0.35)` |

---

## 3. Typography Stack & Scale

```css
--font-sans: 'Manrope', system-ui, -apple-system, sans-serif;
--font-mono: 'DM Mono', monospace;
--font-display: 'Cinzel', serif;
```

1. **Headings & Badges (`Cinzel` / `Manrope` 800):**
   - Brand title: `Cinzel` uppercase, letter-spacing `0.5px`.
   - Card headers: `Manrope` 700/800, uppercase letter-spacing `0.4px`.
2. **Numeric Telemetry & Timestamps (`DM Mono`):**
   - Probabilities (`97%`, `12%`), timestamps (`T+07m`, `12:04:15 UTC`), and coordinates (`21.1458° N, 79.0882° E`) are rendered in monospaced font to eliminate visual jitter during real-time streaming updates.
3. **Body & Rationale (`Manrope` 400/500):**
   - High legibility at 12–14px with line height `1.6` for rapid reading under operational pressure.

---

## 4. Component Patterns & UX Architecture

### 4.1 Operational Topbar
- **Brand Identity:** TantraFiesta gradient-framed pulse icon + "CrisisPulse AI · NAGPUR" with gold hairline underline.
- **Operating Mode Toggle:** Switch between `LIVE OPERATIONS` (green pulse) and `BENCHMARK LAB` (gold accent).
- **Location Selector Pill:** Interactive modal toggle showing current district focus (Nagpur District / Zone).
- **Live Stream Indicator:** Real-time WebSocket connection state with pulsing telemetry dot.
- **Quick Actions:** One-click `Poll Now` (triggers live ingestion) and `Export` (downloads full JSON audit ledger).

### 4.2 District Response Hero Banner
- Prominently displays the current authorized response level (`WATCH`, `PREPARE`, `ALERT`, or `ESCALATE`).
- Dynamic border and glow effect tied to the active posture.
- Dual-encoding: Icon (`RadioTower` / `AlertTriangle`), text label, and descriptive posture subtitle.

### 4.3 Bayesian Hypothesis Monitor
- Visualizes the four mutually exclusive hypotheses:
  - **H1:** Normal conditions / Noise (`#06b6d4`)
  - **H2:** Sensor / Gateway failure (`#a855f7`)
  - **H3:** Isolated incident (`#f59e0b`)
  - **H4:** Cascading emergency crisis (`#ef4444`)
- Dynamic animated probability bars guaranteeing $\sum P(H_i) = 1.00$.
- Historical belief progression area chart showing belief convergence over time.

### 4.4 Response Cost Evaluation & Hysteresis Display
- Renders expected loss bars across all four response strategies.
- Optimal strategy highlighted in bright teal/cyan.
- **Alert Stability & Hysteresis Disclosure:** Transparently displays cooldown status (180s), persistence requirements, and multi-source corroboration gating rules.

### 4.5 The First 10 Minutes Intelligence Lab
Structured into four specialized operational tabs:
1. **Evidence Replay:** Scrubber (0–10 min) with Play/Pause/Step/Reset controls across all 16 standardized scenarios.
2. **The Twin Test Benchmark:**
   - Formal verification banner: Confirms minutes 0–6 are strictly identical across timestamps, source IDs, ordering, probabilities, and actions.
   - Five critical challenge metric cards: Divergence Minute (7), Time to Justified Detection (T+7m), Premature Confidence Penalty (0.00), False Alarm Cost Avoided (+$9.30), and Missed Detection Cost Avoided (+$17.00).
   - Side-by-side split cards comparing Twin A (Genuine Cascade) vs Twin B (Sensor Glitch) at any selected minute.
   - Comprehensive comparative trajectory matrix table.
   - Causal root cause explanation of why Twin A escalated while Twin B was contained.
3. **What-If Counterfactual Simulator:** Interactive hypothetical experiments (weather feed cut, independent police corroboration, cloudburst surge, duplicate retraction) displaying recomputed probabilities and action deltas.
4. **Online Trust Learning & Source Health:** Beta conjugate distribution parameters ($\alpha, \beta$, variance), environmental base-rate drift tracking, and interactive live experiment button.

### 4.6 Multi-Horizon Predictive Forecasts
- Displays the next three plausible causal projections (10, 30, 60 min).
- Ordered causal propagation chains with numbered step badges.
- Data basis tags (`OBSERVED_DATA`, `CAUSAL_RULE`, `STATISTICAL_MODEL`).
- Confidence bands and uncertainty alternative branches.

### 4.7 Live Intelligence Feed
- Provenance badges: `LIVE`, `FORECAST`, `CACHED`, `SYNTHETIC`, `RETRACTED`.
- Retracted and superseded events rendered with strikethrough styling and links to superseding IDs to prevent double-counting.
- Multi-dimensional filtering by search term, hazard category, and data provenance.

---

## 5. Accessibility & Ergonomics

1. **Colorblind-Safe Redundancy:** No operational information is communicated solely through color. Every status, hypothesis, and severity metric includes text labels, icons, and numerical percentages.
2. **Contrast Standards:** Warm Ivory (`#fdfcf7`) on Deep Aubergine (`#0d0714`) achieves a contrast ratio of **16.5:1**, far exceeding the WCAG AAA requirement (7:1).
3. **Motion Sensitivity:** CSS transitions are capped at 0.25s–0.3s to prevent UI lag or motion sickness during rapid data refresh cycles.
4. **Defensive Layout:** Grid containers utilize `minmax()` and `auto-fit` to ensure zero overflow or layout breaking across screen resolutions from 1280px laptops to 4K incident command displays.
