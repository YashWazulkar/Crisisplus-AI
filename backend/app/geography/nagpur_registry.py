"""Authoritative Geographic Registry for Nagpur District and Municipal Corporation (NMC).

Defines administrative hierarchies, zones, wards, known waterlogging hotspots,
critical emergency medical facilities, and hydrological corridors.
"""

from __future__ import annotations
from typing import Any

# Nagpur Geographic Datum and Center (WGS84)
NAGPUR_CENTER_LAT = 21.1458
NAGPUR_CENTER_LON = 79.0882
NAGPUR_DISTRICT_CODE = "505"
NAGPUR_DISTRICT_NAME = "Nagpur"
NAGPUR_STATE = "Maharashtra"

# Authoritative Bounding Boxes (min_lat, min_lon, max_lat, max_lon)
# Nagpur District covers ~9,892 km² across 14 talukas
NAGPUR_DISTRICT_BBOX = (20.5800, 78.2500, 21.7500, 79.6700)

# Nagpur Municipal Corporation (NMC) Urban Area covers ~227.37 km²
NAGPUR_URBAN_BBOX = (21.0500, 79.0000, 21.2400, 79.1800)

# 10 Official Administrative Zones of Nagpur Municipal Corporation (NMC)
# Each zone is mapped to its administrative identifier, headquarters, centroid, and representative localities.
NMC_ZONES: dict[str, dict[str, Any]] = {
    "zone-1-laxmi-nagar": {
        "zone_number": 1,
        "name": "Laxmi Nagar Zone",
        "marathi_name": "लक्ष्मीनगर झोन",
        "centroid": [21.1150, 79.0600],
        "localities": ["Bajaj Nagar", "Pratap Nagar", "Khamla", "Jaitala", "Trimurti Nagar", "Tatya Tope Nagar"],
        "critical_infrastructure": ["Orange City Hospital", "Subhash Nagar Metro", "Ambazari Catchment South"],
        "known_flood_vulnerability": "Moderate (local street ponding at Khamla square and Ring road underpasses)",
    },
    "zone-2-dharampeth": {
        "zone_number": 2,
        "name": "Dharampeth Zone",
        "marathi_name": "धरमपेठ झोन",
        "centroid": [21.1460, 79.0620],
        "localities": ["Civil Lines", "Ramdaspeth", "Shivaji Nagar", "Gokulpeth", "Ambazari", "Ravi Nagar"],
        "critical_infrastructure": ["High Court / District Collectorate", "Care Hospital", "Ambazari Lake & Overflow Dam"],
        "known_flood_vulnerability": "High (Ambazari lake overflow into Nag River origin, Krazy Castle corridor)",
    },
    "zone-3-hanuman-nagar": {
        "zone_number": 3,
        "name": "Hanuman Nagar Zone",
        "marathi_name": "हनुमाननगर झोन",
        "centroid": [21.1180, 79.1020],
        "localities": ["Reshimbagh", "Ayodhya Nagar", "Sakkardara", "Dighori", "Narendra Nagar", "Manewada"],
        "critical_infrastructure": ["Government Medical College & Hospital (GMCH)", "Narendra Nagar R.o.B.", "Tukdoji Putla"],
        "known_flood_vulnerability": "Severe (Narendra Nagar underpass chronic submergence, Sakkardara lake catchment)",
    },
    "zone-4-dhantoli": {
        "zone_number": 4,
        "name": "Dhantoli Zone",
        "marathi_name": "धंतोली झोन",
        "centroid": [21.1380, 79.0850],
        "localities": ["Sitabuldi", "Dhantoli", "Congress Nagar", "Rahate Colony", "Mehadia Square"],
        "critical_infrastructure": ["Sitabuldi Interchange Metro", "Mor Bhavan Bus Terminus", "Nagpur Central Railway Station"],
        "known_flood_vulnerability": "High (Mor Bhavan transit terminal runoff, Sitabuldi market drainage overload)",
    },
    "zone-5-nehru-nagar": {
        "zone_number": 5,
        "name": "Nehru Nagar Zone",
        "marathi_name": "नेहरूनगर झोन",
        "centroid": [21.1290, 79.1280],
        "localities": ["Nandanvan", "Hasanbagh", "Tajbagh", "Wathoda", "Sardar Patel Nagar"],
        "critical_infrastructure": ["Symbiosis International Campus", "Pora River Basin East", "KDK College Road"],
        "known_flood_vulnerability": "Moderate-High (Pora river backflow, low-lying resettlement pockets)",
    },
    "zone-6-gandhibagh": {
        "zone_number": 6,
        "name": "Gandhibagh Zone",
        "marathi_name": "गांधीबाग झोन",
        "centroid": [21.1520, 79.1050],
        "localities": ["Mahal", "Itwari", "Gandhibagh", "Hansapuri", "Badkas Square", "Maskasath"],
        "critical_infrastructure": ["Indira Gandhi Govt Medical College (Mayo Hospital)", "Itwari Commercial Market"],
        "known_flood_vulnerability": "High (Dense historical old city layout, Nag River corridor passing through Mahal/Badkas)",
    },
    "zone-7-satranjipura": {
        "zone_number": 7,
        "name": "Satranjipura Zone",
        "marathi_name": "सतरंजीपुरा झोन",
        "centroid": [21.1630, 79.1120],
        "localities": ["Satranjipura", "Shanti Nagar", "Mehdi Bagh", "Bhandewadi fringe", "Kalamna"],
        "critical_infrastructure": ["Kalamna Agricultural Produce Market (APMC)", "Pili River Confluence"],
        "known_flood_vulnerability": "High (Industrial and wholesale transit corridors, open drain surcharging)",
    },
    "zone-8-lakadganj": {
        "zone_number": 8,
        "name": "Lakadganj Zone",
        "marathi_name": "लकडगंज झोन",
        "centroid": [21.1480, 79.1360],
        "localities": ["Wardhaman Nagar", "Lakadganj", "Pardi", "Surya Nagar", "Bhavani Nagar"],
        "critical_infrastructure": ["Pardi Flyover & Bhandara Road NH-53", "Nag River East Outfall"],
        "known_flood_vulnerability": "Severe (Pardi low-lying depression, Bhandara road arterial submergence)",
    },
    "zone-9-ashi-nagar": {
        "zone_number": 9,
        "name": "Ashi Nagar Zone",
        "marathi_name": "आशीनगर झोन",
        "centroid": [21.1820, 79.1080],
        "localities": ["Indora", "Jaripatka", "Pachpaoli", "Vaishali Nagar", "Nari", "Teka"],
        "critical_infrastructure": ["Pachpaoli Railway Overbridge", "Dr. Ambedkar Hospital", "Pili River Basin"],
        "known_flood_vulnerability": "Severe (Pili River bank breaching during heavy downpours, low-elevation Nari settlement)",
    },
    "zone-10-mangalwari": {
        "zone_number": 10,
        "name": "Mangalwari Zone",
        "marathi_name": "मंगळवारी झोन",
        "centroid": [21.1760, 79.0750],
        "localities": ["Sadar", "Chaoni", "Koradi Road", "Mankapur", "Zingabai Takli", "Borgaon"],
        "critical_infrastructure": ["Mankapur Indoor Sports Complex", "Gaddigodam Underbridge", "Alexis / Max Hospital"],
        "known_flood_vulnerability": "High (Gaddigodam railway underpass, Mankapur underpass on NH-47, Koradi road runoff)",
    },
}

# Documented Chronic Waterlogging Hotspots in Nagpur (Municipal Disaster Plans)
NAGPUR_WATERLOGGING_HOTSPOTS = [
    {
        "id": "hotspot-narendra-nagar",
        "name": "Narendra Nagar Railway Underpass",
        "zone_id": "zone-3-hanuman-nagar",
        "latitude": 21.1072,
        "longitude": 79.0792,
        "drainage_basin": "Pora River Catchment",
        "criticality": "Critical Arterial",
        "submersion_threshold_mm_h": 25.0,
        "impact_description": "Arterial road connecting Ring Road to Wardha Road submerses up to 4 feet; disrupts airport transit.",
    },
    {
        "id": "hotspot-mor-bhavan",
        "name": "Mor Bhavan Bus Terminus & Sitabuldi",
        "zone_id": "zone-4-dhantoli",
        "latitude": 21.1415,
        "longitude": 79.0818,
        "drainage_basin": "Nag River Central Canal",
        "criticality": "Public Transit Hub",
        "submersion_threshold_mm_h": 30.0,
        "impact_description": "Central municipal and MSRTC bus terminal floods; paralyzes city public transit and metro feeder routes.",
    },
    {
        "id": "hotspot-ambazari-overflow",
        "name": "Ambazari Lake Dam & Overflow Spillway",
        "zone_id": "zone-2-dharampeth",
        "latitude": 21.1310,
        "longitude": 79.0490,
        "drainage_basin": "Nag River Headwaters",
        "criticality": "Dam / River Origin",
        "submersion_threshold_mm_h": 40.0,
        "impact_description": "Lake overflow into Nag River downstream; threatens Corporation Colony, Shivaji Nagar, and Shankar Nagar.",
    },
    {
        "id": "hotspot-gaddigodam-underpass",
        "name": "Gaddigodam Railway Underbridge (RUB)",
        "zone_id": "zone-10-mangalwari",
        "latitude": 21.1622,
        "longitude": 79.0798,
        "drainage_basin": "Pili-Nag Water Divider",
        "criticality": "Major Underpass",
        "submersion_threshold_mm_h": 20.0,
        "impact_description": "Low clearance railway underpass waterlogs rapidly; cuts off Sadar from Kamptee road corridor.",
    },
    {
        "id": "hotspot-pardi-nakka",
        "name": "Pardi Naka / Bhandara Road Junction",
        "zone_id": "zone-8-lakadganj",
        "latitude": 21.1450,
        "longitude": 79.1480,
        "drainage_basin": "Nag River Outfall",
        "criticality": "National Highway Corridor (NH-53)",
        "submersion_threshold_mm_h": 30.0,
        "impact_description": "East entrance of Nagpur city waterlogs; delays freight trucks and inter-district ambulance transit.",
    },
    {
        "id": "hotspot-mankapur-square",
        "name": "Mankapur Sports Complex Ring Road Underpass",
        "zone_id": "zone-10-mangalwari",
        "latitude": 21.1895,
        "longitude": 79.0742,
        "drainage_basin": "Pili River North Tributary",
        "criticality": "Highway Underpass (NH-47)",
        "submersion_threshold_mm_h": 25.0,
        "impact_description": "Water ponds under the flyover ramps, causing heavy congestion towards Koradi and Chhindwara.",
    },
    {
        "id": "hotspot-besa-ghogli",
        "name": "Besa-Manewada Junction (South Ring Road)",
        "zone_id": "zone-3-hanuman-nagar",
        "latitude": 21.0920,
        "longitude": 79.0980,
        "drainage_basin": "Pora River Basin",
        "criticality": "Suburban Arterial",
        "submersion_threshold_mm_h": 30.0,
        "impact_description": "Rapid urban expansion without stormwater master drain causes road sheet flow and residential basement inundation.",
    },
]

# Major Healthcare Hubs in Nagpur (Authorized reference points for hospital operational interface)
NAGPUR_HOSPITAL_HUBS = [
    {
        "id": "hosp-gmch-nagpur",
        "name": "Government Medical College & Hospital (GMCH)",
        "zone_id": "zone-3-hanuman-nagar",
        "latitude": 21.1275,
        "longitude": 79.0985,
        "type": "Tertiary Public Government",
        "total_beds": 1400,
        "emergency_beds": 90,
        "trauma_center": True,
        "ambulance_bays": 12,
        "elevation_m": 312,
        "waterlogging_risk": "Low (Elevated Campus)",
    },
    {
        "id": "hosp-mayo-iggmch",
        "name": "Indira Gandhi Govt Medical College (Mayo Hospital)",
        "zone_id": "zone-6-gandhibagh",
        "latitude": 21.1542,
        "longitude": 79.0990,
        "type": "Tertiary Public Government",
        "total_beds": 800,
        "emergency_beds": 60,
        "trauma_center": True,
        "ambulance_bays": 8,
        "elevation_m": 305,
        "waterlogging_risk": "Moderate (Approach road waterlogging near Station)",
    },
    {
        "id": "hosp-aiims-nagpur",
        "name": "All India Institute of Medical Sciences (AIIMS) Nagpur",
        "zone_id": "district-rural-south",
        "latitude": 21.0360,
        "longitude": 79.0270,
        "type": "Apex National Referral",
        "total_beds": 960,
        "emergency_beds": 80,
        "trauma_center": True,
        "ambulance_bays": 14,
        "elevation_m": 325,
        "waterlogging_risk": "Low (MIHAN Planned Drainage)",
    },
    {
        "id": "hosp-kingsway",
        "name": "Kingsway Hospital",
        "zone_id": "zone-4-dhantoli",
        "latitude": 21.1528,
        "longitude": 79.0872,
        "type": "Private Super-Specialty",
        "total_beds": 350,
        "emergency_beds": 35,
        "trauma_center": True,
        "ambulance_bays": 6,
        "elevation_m": 310,
        "waterlogging_risk": "Moderate (Near Station Road)",
    },
    {
        "id": "hosp-orange-city",
        "name": "Orange City Hospital & Research Institute",
        "zone_id": "zone-1-laxmi-nagar",
        "latitude": 21.1120,
        "longitude": 79.0625,
        "type": "Private Multi-Specialty",
        "total_beds": 200,
        "emergency_beds": 25,
        "trauma_center": True,
        "ambulance_bays": 4,
        "elevation_m": 315,
        "waterlogging_risk": "Low",
    },
    {
        "id": "hosp-care-nagpur",
        "name": "Care Hospital (Panchsheel Square)",
        "zone_id": "zone-2-dharampeth",
        "latitude": 21.1405,
        "longitude": 79.0768,
        "type": "Private Multi-Specialty",
        "total_beds": 180,
        "emergency_beds": 20,
        "trauma_center": False,
        "ambulance_bays": 3,
        "elevation_m": 312,
        "waterlogging_risk": "Moderate (Wardha road arterial access)",
    },
]

# Hydrological Corridors traversing Nagpur Urban Area
NAGPUR_HYDROLOGY = [
    {
        "id": "hydro-nag-river",
        "name": "Nag River (नाग नदी)",
        "origin": "Ambazari Lake Overflow (West)",
        "outfall": "Kanhan River Confluence (East)",
        "length_km_urban": 17.0,
        "traversed_zones": ["zone-2-dharampeth", "zone-4-dhantoli", "zone-6-gandhibagh", "zone-8-lakadganj"],
        "critical_culverts": ["Krazy Castle Bridge", "Alankar Talkies Culvert", "Panchsheel Talkies Culvert", "Badkas Square Culvert"],
    },
    {
        "id": "hydro-pili-river",
        "name": "Pili River (पिली नदी)",
        "origin": "Gorewada Lake Spillway (North-West)",
        "outfall": "Kanhan River Confluence (North-East)",
        "length_km_urban": 16.5,
        "traversed_zones": ["zone-10-mangalwari", "zone-9-ashi-nagar", "zone-7-satranjipura"],
        "critical_culverts": ["Mankapur Flyover Bridge", "Indora-Jaripatka Bridge", "Kalamna Bridge"],
    },
    {
        "id": "hydro-pora-river",
        "name": "Pora River (पोरा नदी)",
        "origin": "Sonegaon Lake & Hingna Foothills (South-West)",
        "outfall": "Nag River Tributary (South-East)",
        "length_km_urban": 12.0,
        "traversed_zones": ["zone-1-laxmi-nagar", "zone-3-hanuman-nagar", "zone-5-nehru-nagar"],
        "critical_culverts": ["Airport Ring Road Culvert", "Narendra Nagar Culvert", "Dighori Bridge"],
    },
]
