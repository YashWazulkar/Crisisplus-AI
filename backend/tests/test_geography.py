"""Unit Tests for Nagpur Geographic Configuration and Spatial Filtering."""

import pytest
from app.geography import (
    NagpurSpatialFilter,
    NMC_ZONES,
    NAGPUR_WATERLOGGING_HOTSPOTS,
    NAGPUR_HOSPITAL_HUBS,
    get_nagpur_master_geojson,
    get_nagpur_zones_geojson,
)

def test_nagpur_zones_structure():
    assert len(NMC_ZONES) == 10
    assert "zone-1-laxmi-nagar" in NMC_ZONES
    assert "zone-2-dharampeth" in NMC_ZONES
    assert "zone-3-hanuman-nagar" in NMC_ZONES
    assert "zone-4-dhantoli" in NMC_ZONES
    assert "zone-10-mangalwari" in NMC_ZONES

    for zone_id, meta in NMC_ZONES.items():
        assert "name" in meta
        assert "marathi_name" in meta
        assert "centroid" in meta
        assert len(meta["centroid"]) == 2
        assert 21.0 <= meta["centroid"][0] <= 21.3
        assert 79.0 <= meta["centroid"][1] <= 79.2
        assert len(meta["localities"]) > 0

def test_spatial_filter_urban_nagpur():
    sf = NagpurSpatialFilter()
    # Sitabuldi / Dhantoli center
    res = sf.classify_event(21.1458, 79.0882)
    assert res.is_relevant is True
    assert res.is_urban_nmc is True
    assert res.admin_level == "zone"
    assert res.assigned_zone_id is not None
    assert res.precision == "exact_sensor"

def test_spatial_filter_district_level_separation():
    sf = NagpurSpatialFilter()
    # District-level weather observation from Nagpur RMC
    res = sf.classify_event(21.1458, 79.0882, region_str="Nagpur District", source_is_district_level=True)
    assert res.is_relevant is True
    assert res.precision == "district_level"
    assert res.admin_level == "district"
    assert res.assigned_zone_id is None
    assert "District" in (res.assigned_zone_name or "")

def test_spatial_filter_excludes_out_of_region():
    sf = NagpurSpatialFilter()
    # Mumbai coordinates
    res_mumbai = sf.classify_event(19.0760, 72.8777)
    assert res_mumbai.is_relevant is False
    assert res_mumbai.precision == "out_of_region"
    assert res_mumbai.exclusion_reason is not None
    assert "Nagpur" in res_mumbai.exclusion_reason

    # California coordinates (USGS earthquake sample)
    res_ca = sf.classify_event(40.1, -124.5, event_type="earthquake", magnitude=3.5)
    assert res_ca.is_relevant is False
    assert res_ca.precision == "out_of_region"

def test_spatial_filter_downstream_impact():
    sf = NagpurSpatialFilter()
    # Strong earthquake (M=6.5) 400 km away in central India
    # 400 km north of Nagpur is approx 24.7° N, 79.1° E
    res_quake = sf.classify_event(24.7, 79.0882, event_type="earthquake", magnitude=6.5)
    assert res_quake.is_relevant is True
    assert res_quake.admin_level == "regional_upstream"
    assert res_quake.downstream_impact_rationale is not None

def test_geojson_master_generation():
    master = get_nagpur_master_geojson()
    assert "district_boundary" in master
    assert "urban_boundary" in master
    assert "zones" in master
    assert "hotspots" in master
    assert "hospitals" in master
    assert "hydrology" in master

    zones_fc = get_nagpur_zones_geojson()
    assert zones_fc["type"] == "FeatureCollection"
    assert len(zones_fc["features"]) == 10
