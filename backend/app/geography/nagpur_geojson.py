"""Authoritative GeoJSON Provider for Nagpur District, Municipal Zones, and Critical Infrastructure.

Exports valid GeoJSON FeatureCollections for:
  - Nagpur District Outer Boundary
  - Nagpur Municipal Corporation (NMC) Urban Boundary
  - 10 NMC Administrative Zones
  - Chronic Waterlogging Hotspots
  - Major Emergency Healthcare Centers
  - Key Hydrological Corridors (Nag, Pili, Pora Rivers)
"""

from __future__ import annotations
from typing import Any
from .nagpur_registry import (
    NMC_ZONES,
    NAGPUR_WATERLOGGING_HOTSPOTS,
    NAGPUR_HOSPITAL_HUBS,
    NAGPUR_HYDROLOGY,
)

# 1. Nagpur District Polygon (WGS84 Lon, Lat)
# Envelope around the 14 talukas of Nagpur District
NAGPUR_DISTRICT_FEATURE: dict[str, Any] = {
    "type": "Feature",
    "id": "district-nagpur-505",
    "properties": {
        "district_code": "505",
        "name": "Nagpur District",
        "state": "Maharashtra",
        "area_sq_km": 9892,
        "talukas": 14,
        "population_census_2011": 4653570,
        "monitoring_tier": "district_wide",
        "authority": "District Disaster Management Authority (DDMA), Nagpur",
    },
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [78.4500, 21.6500],
            [78.7500, 21.7500],
            [79.2000, 21.6800],
            [79.5500, 21.5500],
            [79.6700, 21.2500],
            [79.5200, 20.8500],
            [79.3500, 20.5800],
            [78.9500, 20.6500],
            [78.5500, 20.9000],
            [78.3200, 21.2000],
            [78.4500, 21.6500],
        ]],
    },
}

# 2. Nagpur Municipal Corporation (NMC) Urban Boundary Polygon
NAGPUR_URBAN_FEATURE: dict[str, Any] = {
    "type": "Feature",
    "id": "nmc-urban-boundary",
    "properties": {
        "name": "Nagpur Municipal Corporation (NMC)",
        "marathi_name": "नागपूर महानगरपालिका",
        "area_sq_km": 227.37,
        "zones_count": 10,
        "prabhags_count": 38,
        "monitoring_tier": "municipal_urban",
        "authority": "Nagpur Municipal Corporation Disaster Management Cell",
    },
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [79.0350, 21.2150],
            [79.1150, 21.2200],
            [79.1550, 21.1950],
            [79.1750, 21.1550],
            [79.1600, 21.1050],
            [79.1200, 21.0750],
            [79.0550, 21.0700],
            [79.0150, 21.1100],
            [79.0200, 21.1700],
            [79.0350, 21.2150],
        ]],
    },
}

# 3. 10 NMC Administrative Zones Polygons (Realistic spatial coverage across NMC)
ZONE_POLYGONS: dict[str, list[list[float]]] = {
    "zone-1-laxmi-nagar": [
        [79.0200, 21.1300], [79.0750, 21.1350], [79.0800, 21.1000],
        [79.0400, 21.0850], [79.0200, 21.1050], [79.0200, 21.1300]
    ],
    "zone-2-dharampeth": [
        [79.0300, 21.1650], [79.0800, 21.1600], [79.0850, 21.1350],
        [79.0350, 21.1300], [79.0300, 21.1650]
    ],
    "zone-3-hanuman-nagar": [
        [79.0800, 21.1350], [79.1250, 21.1350], [79.1200, 21.0850],
        [79.0750, 21.0850], [79.0800, 21.1350]
    ],
    "zone-4-dhantoli": [
        [79.0750, 21.1500], [79.1000, 21.1500], [79.1000, 21.1250],
        [79.0750, 21.1250], [79.0750, 21.1500]
    ],
    "zone-5-nehru-nagar": [
        [79.1150, 21.1400], [79.1550, 21.1400], [79.1500, 21.1000],
        [79.1100, 21.1000], [79.1150, 21.1400]
    ],
    "zone-6-gandhibagh": [
        [79.0950, 21.1650], [79.1250, 21.1650], [79.1250, 21.1400],
        [79.0950, 21.1400], [79.0950, 21.1650]
    ],
    "zone-7-satranjipura": [
        [79.1000, 21.1800], [79.1350, 21.1800], [79.1300, 21.1550],
        [79.0950, 21.1550], [79.1000, 21.1800]
    ],
    "zone-8-lakadganj": [
        [79.1250, 21.1650], [79.1700, 21.1650], [79.1650, 21.1250],
        [79.1200, 21.1250], [79.1250, 21.1650]
    ],
    "zone-9-ashi-nagar": [
        [79.0900, 21.2100], [79.1350, 21.2100], [79.1300, 21.1750],
        [79.0850, 21.1750], [79.0900, 21.2100]
    ],
    "zone-10-mangalwari": [
        [79.0400, 21.2050], [79.0900, 21.2050], [79.0850, 21.1600],
        [79.0350, 21.1600], [79.0400, 21.2050]
    ],
}


def get_nagpur_zones_geojson() -> dict[str, Any]:
    """Returns GeoJSON FeatureCollection of the 10 NMC administrative zones."""
    features = []
    for zone_id, meta in NMC_ZONES.items():
        coords = ZONE_POLYGONS.get(zone_id, [])
        feature = {
            "type": "Feature",
            "id": zone_id,
            "properties": {
                "zone_id": zone_id,
                "zone_number": meta["zone_number"],
                "name": meta["name"],
                "marathi_name": meta["marathi_name"],
                "centroid": meta["centroid"],
                "localities": meta["localities"],
                "critical_infrastructure": meta["critical_infrastructure"],
                "flood_vulnerability": meta["known_flood_vulnerability"],
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords],
            },
        }
        features.append(feature)
    return {"type": "FeatureCollection", "features": features}


def get_nagpur_hotspots_geojson() -> dict[str, Any]:
    """Returns GeoJSON FeatureCollection of documented chronic waterlogging hotspots."""
    features = []
    for h in NAGPUR_WATERLOGGING_HOTSPOTS:
        features.append({
            "type": "Feature",
            "id": h["id"],
            "properties": {
                "hotspot_id": h["id"],
                "name": h["name"],
                "zone_id": h["zone_id"],
                "drainage_basin": h["drainage_basin"],
                "criticality": h["criticality"],
                "threshold_mm_h": h["submersion_threshold_mm_h"],
                "impact": h["impact_description"],
            },
            "geometry": {
                "type": "Point",
                "coordinates": [h["longitude"], h["latitude"]],
            },
        })
    return {"type": "FeatureCollection", "features": features}


def get_nagpur_hospitals_geojson() -> dict[str, Any]:
    """Returns GeoJSON FeatureCollection of major authorized emergency medical facilities."""
    features = []
    for hosp in NAGPUR_HOSPITAL_HUBS:
        features.append({
            "type": "Feature",
            "id": hosp["id"],
            "properties": {
                "hospital_id": hosp["id"],
                "name": hosp["name"],
                "zone_id": hosp["zone_id"],
                "type": hosp["type"],
                "total_beds": hosp["total_beds"],
                "emergency_beds": hosp["emergency_beds"],
                "trauma_center": hosp["trauma_center"],
                "ambulance_bays": hosp["ambulance_bays"],
                "waterlogging_risk": hosp["waterlogging_risk"],
            },
            "geometry": {
                "type": "Point",
                "coordinates": [hosp["longitude"], hosp["latitude"]],
            },
        })
    return {"type": "FeatureCollection", "features": features}


def get_nagpur_hydrology_geojson() -> dict[str, Any]:
    """Returns GeoJSON LineString corridors for Nag, Pili, and Pora Rivers."""
    # Approximate river channel coordinates traversing the city
    river_paths = {
        "hydro-nag-river": [
            [79.0490, 21.1310], [79.0680, 21.1360], [79.0850, 21.1400],
            [79.1020, 21.1450], [79.1240, 21.1460], [79.1550, 21.1480], [79.1850, 21.1520]
        ],
        "hydro-pili-river": [
            [79.0380, 21.1920], [79.0720, 21.1880], [79.1050, 21.1850],
            [79.1320, 21.1820], [79.1650, 21.1780], [79.1920, 21.1750]
        ],
        "hydro-pora-river": [
            [79.0350, 21.0850], [79.0680, 21.0920], [79.0980, 21.1010],
            [79.1280, 21.1120], [79.1580, 21.1250]
        ],
    }

    features = []
    for hydro in NAGPUR_HYDROLOGY:
        coords = river_paths.get(hydro["id"], [])
        features.append({
            "type": "Feature",
            "id": hydro["id"],
            "properties": {
                "river_id": hydro["id"],
                "name": hydro["name"],
                "origin": hydro["origin"],
                "outfall": hydro["outfall"],
                "length_km": hydro["length_km_urban"],
                "culverts": hydro["critical_culverts"],
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coords,
            },
        })
    return {"type": "FeatureCollection", "features": features}


def get_nagpur_master_geojson() -> dict[str, Any]:
    """Returns composite multi-layer GeoJSON object for operational GIS clients."""
    return {
        "district_boundary": NAGPUR_DISTRICT_FEATURE,
        "urban_boundary": NAGPUR_URBAN_FEATURE,
        "zones": get_nagpur_zones_geojson(),
        "hotspots": get_nagpur_hotspots_geojson(),
        "hospitals": get_nagpur_hospitals_geojson(),
        "hydrology": get_nagpur_hydrology_geojson(),
    }
