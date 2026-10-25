# CrisisPulse AI · Data Sources & External Ingestion Connectors

This document provides a comprehensive operational audit and specification of the 8 external intelligence feeds integrated into CrisisPulse AI for Nagpur District and the Nagpur Municipal Corporation (NMC) urban area.

---

## Provenance Model & Anti-Fabrication Guarantees

CrisisPulse AI enforces strict transparency regarding the origin and quality of every observation. The platform categorizes incoming signals into one of five standard provenance states:

1. **`LIVE`**: Direct, real-time telemetry received from an external instrument or authoritative municipal API within its valid temporal window.
2. **`FORECAST`**: Numerical weather prediction model output (e.g. Open-Meteo HRRR/ECMWF) projecting future conditions; never misrepresented as current rainfall.
3. **`CACHED`**: Reference or historical baseline data served with explicit disclosure when live API credentials are unconfigured or remote services are unavailable.
4. **`UNVERIFIED`**: Single-source, uncorroborated reports pending cross-sensor corroboration.
5. **`SYNTHETIC`**: Deterministic benchmark scenarios generated exclusively inside the First-10-Minute Intelligence Lab.

---

## Connector Directory

### 1. India Meteorological Department (IMD) / RMC Nagpur
- **Primary Role:** Official weather warnings, nowcasts, and meteorological observations for Nagpur District.
- **Official Documentation:** [IMD Public API Reference](https://api.imd.gov.in/public/api_reference.html)
- **Regional Centre:** Regional Meteorological Centre (RMC), Nagpur (Sonegaon Airport).
- **Endpoint Structure:** `https://api.imd.gov.in/v1/district_warning/{district_code}` (District Code 106 = Nagpur).
- **Authentication:** Bearer token via `IMD_API_KEY`.
- **Geographic Coverage:** Nagpur District-wide (`geographic_precision: district_level`, `admin_level: district`).
- **Update Frequency:** Every 5 minutes (warnings updated every 3 to 6 hours or upon convective nowcast issuance).
- **Severity Mapping:**
  - `GREEN` (No Warning): Normal operations (severity: 0.10)
  - `YELLOW` (Be Updated): Watch advisory (severity: 0.35)
  - `ORANGE` (Be Prepared): Prepare advisory (severity: 0.65)
  - `RED` (Take Action): Critical severe weather warning (severity: 0.90)
- **Fallback Behavior:** If `IMD_API_KEY` is not configured, the adapter transitions to `awaiting_api_credentials` and serves verified RMC Nagpur reference bulletins labeled with `data_provenance: CACHED`. It never synthesizes false live warnings.

---

### 2. Open-Meteo High-Resolution Weather & Forecasts
- **Primary Role:** High-frequency ambient weather telemetry, rainfall rates, wind gusts, and precipitation forecasts.
- **Official Documentation:** [Open-Meteo Weather API](https://open-meteo.com/en/docs)
- **Endpoint Structure:** `https://api.open-meteo.com/v1/forecast?latitude=21.1458&longitude=79.0882&current=temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m,wind_gusts_10m&hourly=precipitation,rain&forecast_days=1`
- **Authentication:** None required (Open access for non-commercial research under CC-BY 4.0).
- **Geographic Coverage:** Monitored centroid: Nagpur Zero Mile Stone (`21.1458° N, 79.0882° E`).
- **Update Frequency:** Polled every 60 seconds (model grid updates hourly).
- **Telemetry Breakdown:**
  - `rain > 0 mm`: Emitted as `rainfall` event (`data_provenance: LIVE`).
  - `wind_gusts_10m > 40 km/h`: Emitted as `wind_gust` event (`data_provenance: LIVE`).
  - `hourly.precipitation`: Emitted as short-term forecast horizons (`data_provenance: FORECAST`).
- **Data Provenance Enforcement:** Model forecasts are strictly tagged with `data_provenance: FORECAST` and never merged with gauge observations.

---

### 3. Nagpur Municipal Corporation (NMC) Stormwater Drainage
- **Primary Role:** Urban hydrology, culvert water level sensors, and chronic flood hotspot monitoring.
- **Underlying Infrastructure:** Nagpur Smart City IoT stormwater sensor network and NMC Flood Control Cell telemetry.
- **Endpoint Structure:** `NMC_DRAINAGE_IOT_URL` (configurable in `.env`).
- **Monitored Hotspots:**
  1. **Narendra Nagar Railway Underpass:** Low-clearance culvert; critical submersion threshold: 25 mm/h.
  2. **Mor Bhavan / Sitabuldi Interchange:** Urban low point near Nag River basin; threshold: 35 mm/h.
  3. **Ambazari Lake Overflow Canal:** Submergence risk for Corporation Colony / Verma Layout; threshold: 40 mm/h.
  4. **Gaddigodam Railway Underpass:** Low railway dip connecting Kamptee Road; threshold: 25 mm/h.
  5. **Pardi Octroi Post:** Bhandara Road drainage bottleneck; threshold: 30 mm/h.
  6. **Mankapur Sports Complex Dip:** Koradi arterial underpass; threshold: 35 mm/h.
  7. **Besa-Manewada Ring Road Junction:** Rapid stormwater ponding zone; threshold: 30 mm/h.
- **Fallback Behavior:** Evaluates deterministic water level and overflow models based on cumulative rainfall telemetry if municipal IoT API credentials are unset.

---

### 4. Nagpur Emergency Hospital Operational Capacity
- **Primary Role:** Trauma center surge capacity, emergency bed occupancy, and ambulance diversion detection.
- **Monitored Healthcare Facilities:**
  1. **GMCH Nagpur (Government Medical College & Hospital):** 1,400 beds; Level 1 Trauma Center.
  2. **Indira Gandhi Government Medical College (Mayo Hospital):** 800 beds; North-Central emergency hub.
  3. **AIIMS Nagpur (MIHAN):** 750 beds; Tertiary referral trauma facility.
  4. **Kingsway Hospitals:** 300 beds; Central Railway Station junction.
  5. **Orange City Hospital & Research Institute:** 150 beds; South-West emergency corridor.
  6. **Care Hospital (Ramdaspeth):** 105 beds; Central trauma and cardiac care.
- **Privacy Safeguards:** Only aggregate capacity percentages and mass casualty diversion flags are processed. Absolutely zero patient identifiable information (PII) is stored or requested.

---

### 5. Nagpur Traffic Police & Transit Disruption Feed
- **Primary Role:** Arterial transit latency, flood-induced underpass closures, and emergency vehicle routing bottlenecks.
- **Monitored Arterials:**
  - Wardha Road (GMCH & AIIMS emergency transit corridor).
  - Central Avenue (East-West transit through Gandhibagh/Itwari).
  - Ring Road (Outer perimeter heavy vehicle bypass).
  - Koradi Road (Northern gateway to power corridor).
- **Incident Detection:** Triggers `road_flooding` and `ambulance_delay` events when vehicle speeds drop below 8 km/h or when water levels close railway underpasses.

---

### 6. NASA FIRMS (Active Fire / Thermal Anomaly Satellite VIIRS)
- **Primary Role:** Detection of industrial fires, wildland-urban interface blazes, and forest fringe hotspots.
- **Official Documentation:** [NASA FIRMS API Reference](https://firms.modaps.eosdis.nasa.gov/api/)
- **Instruments:** VIIRS (Suomi NPP & NOAA-20) 375m high-resolution active fire product.
- **Spatial Constraint:** Bounding box clipped to Nagpur District (`20.58° N, 78.25° E` to `21.75° N, 79.67° E`).
- **Update Frequency:** Polled every 300 seconds (satellite pass frequency: 2 to 4 passes per 24 hours).
- **Authentication:** Registered `FIRMS_MAP_KEY`.
- **Fallback Behavior:** If `FIRMS_MAP_KEY` is empty, serves verified archival reference samples from Nagpur District forest fringe (Umred Karhandla / Ramtek) tagged as `CACHED` and `awaiting_api_key`.

---

### 7. USGS Earthquake Hazards Program
- **Primary Role:** Detection of seismic events across Central India and Maharashtra.
- **Official Documentation:** [USGS GeoJSON Feed](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)
- **Spatial Filtering Rules:**
  - Global events outside Central India are dropped at ingestion.
  - Regional seismic events within 300 km of Nagpur are admitted only if `magnitude >= 4.0` (downstream felt shock criteria).
  - Events located inside Nagpur District are admitted if `magnitude >= 2.5`.

---

### 8. Global Disaster Alert and Coordination System (GDACS)
- **Primary Role:** Multihazard international disaster alerts (tropical cyclones, major floods, dam breaks).
- **Official Documentation:** [GDACS Public RSS/GeoJSON Feed](https://www.gdacs.org/xml/rss.xml)
- **Spatial Filtering Rules:**
  - Global disasters outside Maharashtra/Central India are excluded.
  - Events within 150 km of Nagpur or upstream river basin flood alerts with documented downstream impacts on Nagpur are admitted with `geographic_precision: approximate`.

---

## Connector Health & Stale-Feed Policy

Each connector is instrumented with an automated health monitor that evaluates:
- **`healthy`**: Successful fetch within the expected polling interval with zero communication errors.
- **`stale`**: Last successful observation older than 2× the configured polling interval.
- **`awaiting_api_credentials` / `awaiting_api_key`**: API key not configured in `.env`; running in transparent reference fallback mode.
- **`degraded` / `failed`**: Network timeout or HTTP error code returned from upstream provider.

The platform continuously displays the composite monitoring status (`LIVE`, `MIXED`, `DEGRADED`, `OFFLINE`) in the Operational Header.
