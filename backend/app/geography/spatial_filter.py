"""Nagpur Operational Spatial Filter and Geographic Classifier.

Performs point-in-polygon, bounding-box, and proximity checks to enforce that only
observations relevant to the configured Nagpur monitoring area enter the operational assessment.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Literal
from .nagpur_registry import (
    NAGPUR_DISTRICT_BBOX,
    NAGPUR_URBAN_BBOX,
    NAGPUR_CENTER_LAT,
    NAGPUR_CENTER_LON,
    NMC_ZONES,
)
from .nagpur_geojson import (
    NAGPUR_DISTRICT_FEATURE,
    NAGPUR_URBAN_FEATURE,
    ZONE_POLYGONS,
)

PrecisionLevel = Literal[
    "exact_sensor",
    "hotspot_level",
    "zone_level",
    "district_level",
    "approximate",
    "unresolved",
    "out_of_region",
]

AdminLevel = Literal[
    "point",
    "hotspot",
    "zone",
    "municipal_urban",
    "district",
    "regional_upstream",
    "unresolved",
]


@dataclass
class SpatialClassification:
    is_relevant: bool
    precision: PrecisionLevel
    admin_level: AdminLevel
    assigned_zone_id: str | None
    assigned_zone_name: str | None
    distance_to_center_km: float
    is_urban_nmc: bool
    is_district_wide: bool
    downstream_impact_rationale: str | None
    exclusion_reason: str | None


def point_in_polygon(lat: float, lon: float, polygon_coords: list[list[float]]) -> bool:
    """Standard ray-casting algorithm to determine if a point (lat, lon) is inside a polygon.
    polygon_coords are formatted as [[lon, lat], [lon, lat], ...] as per GeoJSON specification.
    """
    inside = False
    n = len(polygon_coords)
    if n < 3:
        return False

    p1x, p1y = polygon_coords[0][0], polygon_coords[0][1]
    for i in range(1, n + 1):
        p2x, p2y = polygon_coords[i % n][0], polygon_coords[i % n][1]
        if lat > min(p1y, p2y):
            if lat <= max(p1y, p2y):
                if lon <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (lat - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or lon <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    )
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


class NagpurSpatialFilter:
    """Enforces geographic filtering rules for incoming observations."""

    def __init__(self):
        self.district_poly = NAGPUR_DISTRICT_FEATURE["geometry"]["coordinates"][0]
        self.urban_poly = NAGPUR_URBAN_FEATURE["geometry"]["coordinates"][0]
        self.zone_polys = ZONE_POLYGONS

    def classify_event(
        self,
        lat: float | None,
        lon: float | None,
        region_str: str | None = None,
        event_type: str | None = None,
        magnitude: float | None = None,
        source_is_district_level: bool = False,
    ) -> SpatialClassification:
        """Classifies an incoming event's spatial relevance to Nagpur.
        
        Strict rules:
        - If lat/lon are missing or unresolved, check if region text refers explicitly to Nagpur.
        - Check bounding box first.
        - Determine if point is within NMC urban boundary or wider Nagpur district boundary.
        - If inside urban area, resolve specific NMC zone (Laxmi Nagar, Dharampeth, etc.).
        - If outside district boundary, check for documented downstream impacts (e.g. major regional seismic shock or upstream dam discharge).
        """
        # Case A: Missing or unresolved coordinates
        if lat is None or lon is None or (lat == 0.0 and lon == 0.0) or math.isnan(lat) or math.isnan(lon):
            if region_str and "nagpur" in region_str.lower():
                return SpatialClassification(
                    is_relevant=True,
                    precision="district_level",
                    admin_level="district",
                    assigned_zone_id=None,
                    assigned_zone_name="Nagpur District (District-Wide)",
                    distance_to_center_km=0.0,
                    is_urban_nmc=False,
                    is_district_wide=True,
                    downstream_impact_rationale="Resolved via regional bulletin text explicitly mentioning Nagpur.",
                    exclusion_reason=None,
                )
            return SpatialClassification(
                is_relevant=False,
                precision="unresolved",
                admin_level="unresolved",
                assigned_zone_id=None,
                assigned_zone_name=None,
                distance_to_center_km=9999.0,
                is_urban_nmc=False,
                is_district_wide=False,
                downstream_impact_rationale=None,
                exclusion_reason="Coordinates unresolved and region text lacks Nagpur identifier.",
            )

        dist_to_center = haversine_km(lat, lon, NAGPUR_CENTER_LAT, NAGPUR_CENTER_LON)

        # Case B: Explicit district-level sources (e.g. IMD District Weather Bulletin)
        # Even if given single coordinates (e.g., Nagpur RMC Airport), do not pretend it is street-level.
        if source_is_district_level:
            in_district = point_in_polygon(lat, lon, self.district_poly) or dist_to_center <= 60.0
            if in_district or (region_str and "nagpur" in region_str.lower()):
                return SpatialClassification(
                    is_relevant=True,
                    precision="district_level",
                    admin_level="district",
                    assigned_zone_id=None,
                    assigned_zone_name="Nagpur District (District-Wide)",
                    distance_to_center_km=dist_to_center,
                    is_urban_nmc=False,
                    is_district_wide=True,
                    downstream_impact_rationale=None,
                    exclusion_reason=None,
                )

        # Case C: Check if point is inside NMC Urban Boundary
        min_ulat, min_ulon, max_ulat, max_ulon = NAGPUR_URBAN_BBOX
        in_urban_bbox = (min_ulat <= lat <= max_ulat) and (min_ulon <= lon <= max_ulon)
        in_urban = in_urban_bbox and point_in_polygon(lat, lon, self.urban_poly)

        if in_urban:
            # Match specific NMC zone polygon
            matched_zone_id = None
            for zone_id, poly in self.zone_polys.items():
                if point_in_polygon(lat, lon, poly):
                    matched_zone_id = zone_id
                    break

            # Fallback to closest zone centroid if right on boundary
            if not matched_zone_id:
                closest_zone = min(
                    NMC_ZONES.items(),
                    key=lambda item: haversine_km(lat, lon, item[1]["centroid"][0], item[1]["centroid"][1]),
                )
                matched_zone_id = closest_zone[0]

            zone_name = NMC_ZONES[matched_zone_id]["name"]
            return SpatialClassification(
                is_relevant=True,
                precision="exact_sensor",
                admin_level="zone",
                assigned_zone_id=matched_zone_id,
                assigned_zone_name=zone_name,
                distance_to_center_km=dist_to_center,
                is_urban_nmc=True,
                is_district_wide=False,
                downstream_impact_rationale=None,
                exclusion_reason=None,
            )

        # Case D: Check if point is inside Nagpur District Boundary
        min_dlat, min_dlon, max_dlat, max_dlon = NAGPUR_DISTRICT_BBOX
        in_district_bbox = (min_dlat <= lat <= max_dlat) and (min_dlon <= lon <= max_dlon)
        in_district = in_district_bbox and point_in_polygon(lat, lon, self.district_poly)

        if in_district:
            return SpatialClassification(
                is_relevant=True,
                precision="approximate",
                admin_level="district",
                assigned_zone_id="district-rural-fringe",
                assigned_zone_name="Nagpur District (Peri-Urban / Rural)",
                distance_to_center_km=dist_to_center,
                is_urban_nmc=False,
                is_district_wide=False,
                downstream_impact_rationale="Observation situated within outer Nagpur District taluka boundary.",
                exclusion_reason=None,
            )

        # Case E: Downstream impact checks for out-of-boundary events
        # 1. Seismic shocks within felt distance (M >= 4.5 within 250 km, or M >= 6.0 within 600 km)
        if event_type == "earthquake" and magnitude is not None:
            if (magnitude >= 4.5 and dist_to_center <= 250.0) or (magnitude >= 6.0 and dist_to_center <= 600.0):
                return SpatialClassification(
                    is_relevant=True,
                    precision="approximate",
                    admin_level="regional_upstream",
                    assigned_zone_id=None,
                    assigned_zone_name="Regional Upstream Seismic Impact",
                    distance_to_center_km=dist_to_center,
                    is_urban_nmc=False,
                    is_district_wide=True,
                    downstream_impact_rationale=(
                        f"Magnitude {magnitude} regional earthquake at {dist_to_center:.1f} km distance; "
                        "has plausible ground-shaking propagation into Nagpur district."
                    ),
                    exclusion_reason=None,
                )

        # 2. Major cyclonic or regional flood alerts within 120 km (e.g. Wardha / Bhandara / Pench basin)
        if event_type in ("flood", "cyclone") and dist_to_center <= 120.0:
            return SpatialClassification(
                is_relevant=True,
                precision="approximate",
                admin_level="regional_upstream",
                assigned_zone_id=None,
                assigned_zone_name="Regional Upstream Hydrological Catchment",
                distance_to_center_km=dist_to_center,
                is_urban_nmc=False,
                is_district_wide=True,
                downstream_impact_rationale=(
                    f"Regional {event_type} within {dist_to_center:.1f} km; upstream Kanhan/Pench river "
                    "catchment directly drains into Nagpur district water systems."
                ),
                exclusion_reason=None,
            )

        # Case F: Definitely out-of-region -> Exclude from operational assessments
        return SpatialClassification(
            is_relevant=False,
            precision="out_of_region",
            admin_level="unresolved",
            assigned_zone_id=None,
            assigned_zone_name=None,
            distance_to_center_km=dist_to_center,
            is_urban_nmc=False,
            is_district_wide=False,
            downstream_impact_rationale=None,
            exclusion_reason=(
                f"Location ({lat:.3f}, {lon:.3f}) is {dist_to_center:.1f} km from Nagpur center, "
                "outside configured district boundaries with no documented downstream hazard."
            ),
        )
