"""Nagpur Operational Geography Package."""

from .nagpur_registry import (
    NAGPUR_CENTER_LAT,
    NAGPUR_CENTER_LON,
    NAGPUR_DISTRICT_CODE,
    NAGPUR_DISTRICT_NAME,
    NAGPUR_STATE,
    NAGPUR_DISTRICT_BBOX,
    NAGPUR_URBAN_BBOX,
    NMC_ZONES,
    NAGPUR_WATERLOGGING_HOTSPOTS,
    NAGPUR_HOSPITAL_HUBS,
    NAGPUR_HYDROLOGY,
)
from .nagpur_geojson import (
    get_nagpur_master_geojson,
    get_nagpur_zones_geojson,
    get_nagpur_hotspots_geojson,
    get_nagpur_hospitals_geojson,
    get_nagpur_hydrology_geojson,
)
from .spatial_filter import NagpurSpatialFilter, SpatialClassification
