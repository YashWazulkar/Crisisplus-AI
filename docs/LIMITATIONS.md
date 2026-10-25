# CrisisPulse AI 2.0 — Known Limitations & Responsible Operation

## 1. Explicit Disclaimers and Non-Autonomous Dispatch

> [!CAUTION]
> **NOT FOR AUTONOMOUS EMERGENCY DISPATCH**
> CrisisPulse AI is a decision-support, situational awareness, and predictive intelligence prototype. It must **never** be connected directly to autonomous 911/112 public alerting systems, siren networks, or emergency responder dispatch queues without human authorization. All high-impact operational recommendations require verified human review by authorized emergency management personnel.

---

## 2. Technical and Modeling Limitations

1. **No Earthquake Pre-cognition**:
   - The USGS Earthquake Hazards Program feed detects seismic waves *after* fault rupture has occurred.
   - CrisisPulse AI does **not** claim to predict the exact time, magnitude, or epicenter of an unruptured earthquake before physical seismic wave propagation.

2. **Mesoscale Weather Resolution**:
   - Open-Meteo observations and radar integrations reflect atmospheric model grids (typically 1–5 km spatial resolution).
   - Micro-topographic phenomena (such as a blocked municipal storm drain or localized basement flooding under an overpass) cannot be measured solely from satellite or grid radar telemetry.

3. **Sensor Bias and Infrastructure Failures**:
   - Physical telemetry can suffer from localized power blackouts, cellular carrier degradation, or sensor calibration drift.
   - While the Bayesian engine down-weights uncorroborated single-source spikes, widespread power grid collapse can create an observation vacuum. The system does not interpret the absence of observations as proof that conditions are safe.

4. **Satellite Wildfire Latency**:
   - NASA FIRMS active fire hotspots rely on polar-orbiting satellite passes (VIIRS / MODIS).
   - Observations have an inherent latency of 1 to 3 hours depending on satellite overpass schedules. Active fire detections reflect thermal radiative anomalies and must be distinguished from confirmed ground blazes.

5. **Regional Government Portal SSL Constraints**:
   - In India, official web portals from the India Meteorological Department (IMD) and National Disaster Management Authority (NDMA / Sachet) frequently utilize Indian National Informatics Centre (NIC) root CA certificates.
   - Standard commercial operating system trust stores may reject these connections with `SSL: CERTIFICATE_VERIFY_FAILED`. When this occurs, CrisisPulse AI reports `status: degraded` or `status: unavailable` with clear diagnostics, and never fabricates fake emergency data.

---

## 3. Ethical Considerations and Privacy

- CrisisPulse AI processes only public, official, or anonymized regional telemetry.
- No personal identifying information (PII), private cellular GPS tracking, or private social media posts are harvested or stored.
- All intelligence outputs provide full evidence provenance, citing original URLs, timestamps, and quality weights.
