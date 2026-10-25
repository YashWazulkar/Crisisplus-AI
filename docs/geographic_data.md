# CrisisPulse AI · Nagpur Operational Geographic Specification

This document details the centralized geographic registry, boundary geometries, administrative zoning, and spatial filtering rules implemented for Nagpur District and the Nagpur Municipal Corporation (NMC).

---

## 1. Geographic Scope & Hierarchy

CrisisPulse AI strictly maintains the separation between two distinct administrative levels:
1. **Nagpur District (District-Wide Scope)**: Covering 9,892 km² across 14 talukas, bounding coordinates:
   - Latitude: `20.58° N` to `21.75° N`
   - Longitude: `78.25° E` to `79.67° E`
2. **Nagpur City / NMC (Municipal Urban Scope)**: Covering 227 km² organized into 10 administrative zones, bounding coordinates:
   - Latitude: `21.06° N` to `21.23° N`
   - Longitude: `79.00° E` to `79.18° E`

**Zero Mile Stone Centroid:** `21.1458° N, 79.0882° E` (The geographical center of India, located in Sitabuldi, Nagpur).

---

## 2. NMC 10 Administrative Zones

The Nagpur Municipal Corporation administers the city through 10 official zones:

| Zone ID | Official English Name | Marathi Transliteration | Centroid (Lat, Lon) | Approx. Pop. | Key Localities & Landmarks |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`zone_1`** | Laxmi Nagar | लक्ष्मीनगर | `(21.1150, 79.0620)` | 260,000 | Bajaj Nagar, Pratap Nagar, Shraddhanand Peth, VNIT Campus |
| **`zone_2`** | Dharampeth | धरमपेठ | `(21.1420, 79.0550)` | 230,000 | Gokulpeth, Ram Nagar, Civil Lines, Ambazari, High Court |
| **`zone_3`** | Hanuman Nagar | हनुमान नगर | `(21.1180, 79.0980)` | 275,000 | Medical Square, GMCH Campus, Reshimbagh, Rambagh, Sakkardara |
| **`zone_4`** | Dhantoli | धंतोली | `(21.1300, 79.0820)` | 240,000 | Sitabuldi, Congress Nagar, Rahate Colony, Narendra Nagar Underpass |
| **`zone_5`** | Nehru Nagar | नेहरू नगर | `(21.1250, 79.1250)` | 280,000 | Nandanvan, Dighori, Hasanbagh, Kharbi Road, Tajbagh |
| **`zone_6`** | Gandhibagh | गांधीबाग | `(21.1480, 79.1020)` | 250,000 | Itwari, Mahal, Hansapuri, Central Avenue, Badkas Chowk |
| **`zone_7`** | Satranjipura | सतरंजीपुरा | `(21.1620, 79.1120)` | 220,000 | Shanti Nagar, Maskasath, Mayo Hospital East, Itwari Railway Station |
| **`zone_8`** | Lakadganj | लकडगंज | `(21.1490, 79.1350)` | 265,000 | Pardi, Wardhaman Nagar, Old Bagadganj, Bhandara Road |
| **`zone_9`** | Ashi Nagar | आसी नगर | `(21.1820, 79.1050)` | 290,000 | Jaripatka, Misal Layout, Teka Naka, Kamptee Road North |
| **`zone_10`**| Mangalwari | मंगळवारी | `(21.1750, 79.0720)` | 255,000 | Sadar, Chaoni, Mankapur, Zingabai Takli, Koradi Gateway |

---

## 3. Chronic Waterlogging Hotspots

Urban flood history and NMC municipal reports identify 7 chronic waterlogging bottlenecks:

1. **Narendra Nagar Railway Underpass (Zone 4 - Dhantoli)**
   - Centroid: `21.1095° N, 79.0772° E`
   - Critical Inundation Threshold: **25.0 mm/h**
   - Impact: Submersion blocks Wardha Road arterial transit to AIIMS and MIHAN, severing South Nagpur connectivity.
2. **Mor Bhavan / Sitabuldi Interchange (Zone 4 - Dhantoli)**
   - Centroid: `21.1425° N, 79.0838° E`
   - Critical Inundation Threshold: **35.0 mm/h**
   - Impact: Core public bus transit terminus inundation causing city-wide transit paralysis.
3. **Ambazari Lake Overflow Canal (Zone 2 - Dharampeth)**
   - Centroid: `21.1310° N, 79.0490° E`
   - Critical Inundation Threshold: **40.0 mm/h**
   - Impact: Discharge spills into Nag River corridor, causing residential backflow in Corporation Colony and Verma Layout.
4. **Gaddigodam Railway Underpass (Zone 10 - Mangalwari)**
   - Centroid: `21.1660° N, 79.0815° E`
   - Critical Inundation Threshold: **25.0 mm/h**
   - Impact: Low-clearance railway culvert cuts off Sadar and Kamptee Road connectivity.
5. **Pardi Octroi Post Bottleneck (Zone 8 - Lakadganj)**
   - Centroid: `21.1480° N, 79.1550° E`
   - Critical Inundation Threshold: **30.0 mm/h**
   - Impact: Heavy logistics gridlock on NH-53 (Bhandara Road) impacting industrial freight corridor.
6. **Mankapur Sports Complex Railway Dip (Zone 10 - Mangalwari)**
   - Centroid: `21.1890° N, 79.0750° E`
   - Critical Inundation Threshold: **35.0 mm/h**
   - Impact: Floods Koradi Road arterial, isolating north suburban residential layouts.
7. **Besa-Manewada Ring Road Junction (Zone 4 / 5 Boundary)**
   - Centroid: `21.0980° N, 79.1020° E`
   - Critical Inundation Threshold: **30.0 mm/h**
   - Impact: Major South Nagpur ring road intersection becomes impassable, causing outer perimeter gridlock.

---

## 4. Emergency Healthcare & Trauma Centers

The platform models critical healthcare capacity across 6 major tertiary hospitals:

| Facility Name | Zone ID | Centroid (Lat, Lon) | Normal Bed Capacity | Trauma Level | Role in Mass Casualty |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GMCH Nagpur** | `zone_3` | `(21.1275, 79.0985)` | 1,400 | Level 1 | Premier public trauma center for Vidarbha region |
| **Mayo Hospital (IGGMC)** | `zone_7` | `(21.1575, 79.0945)` | 800 | Level 1 | Major government emergency hospital serving North Nagpur |
| **AIIMS Nagpur** | Outer (`zone_4` corridor) | `(21.0420, 79.0350)` | 750 | Tertiary Trauma | Apex referral institution located in MIHAN |
| **Kingsway Hospitals** | `zone_4` / `zone_6` | `(21.1520, 79.0880)` | 300 | Multi-Specialty | Railway Station junction trauma reception |
| **Orange City Hospital**| `zone_4` | `(21.1180, 79.0750)` | 150 | Critical Care | South-West accident and emergency corridor |
| **Care Hospital** | `zone_4` | `(21.1350, 79.0720)` | 105 | Super-Specialty | Ramdaspeth central emergency and cardiac unit |

---

## 5. Hydrological River Corridors

Nagpur's natural stormwater drainage relies on three primary river basins modeled as GeoJSON LineStrings:
1. **Nag River Corridor:** Originates from Ambazari Lake overflow, winds through Shankar Nagar, Sitabuldi, Congress Nagar, Mahal, and drains eastward into Kanhan River.
2. **Pili River Corridor:** Traverses northern Nagpur through Gorewada overflow, Mankapur, Jaripatka, and Pardi.
3. **Pora River Corridor:** Traverses southern fringe through Sonegaon, Besa, and Manewada.

---

## 6. Spatial Filtering & Geographic Precision Model

Every incoming event is classified by `NagpurSpatialFilter`:

```python
class SpatialClassification:
    is_relevant: bool
    precision: str # 'exact_sensor' | 'hotspot_level' | 'zone_level' | 'district_level' | 'approximate' | 'unresolved' | 'out_of_region'
    admin_level: str # 'site' | 'zone' | 'district' | 'regional'
    assigned_zone_id: Optional[str] # e.g. 'zone_4'
    assigned_zone_name: Optional[str] # e.g. 'Dhantoli'
    distance_km: float
    is_downstream_impact: bool
```

### Classification Rules:
1. **Inside NMC Zone Polygon:** Assigned to the specific zone (`zone_1` - `zone_10`) with `precision = "zone_level"` (or `"exact_sensor"` if sensor coordinates match an instrument).
2. **Inside Nagpur District Bounding Box:** Assigned to `Nagpur District (District-Wide)` with `precision = "district_level"`. It is never silently localized to a specific ward or street.
3. **Outside Nagpur District:**
   - Evaluated for downstream impact (e.g. regional seismic shock $\ge 4.0$ within 300 km, or upstream reservoir alert within 150 km).
   - If downstream impact exists, marked as `is_relevant = True`, `precision = "approximate"`, `admin_level = "regional"`.
   - If no downstream impact, marked as `is_relevant = False`, `precision = "out_of_region"`, and excluded from operational risk assessments.
