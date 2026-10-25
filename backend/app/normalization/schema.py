"""Unified Event Schema for CrisisPulse AI: Nagpur Edition.

Provides standard representation for all incoming emergency, environmental,
and infrastructure signals across public and municipal feeds, with strict
geographic classification and verifiable data provenance.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator
import uuid

EventCategory = Literal[
    "rainfall",
    "wind_gust",
    "severe_weather",
    "temperature_anomaly",
    "earthquake",
    "wildfire",
    "flood",
    "cyclone",
    "water_level",
    "traffic_speed",
    "road_flooding",
    "ambulance_delay",
    "hospital_demand",
    "drainage_overflow",
    "sensor_failure",
    "gateway_failure",
    "citizen_report",
    "power_outage",
    "source_recovered",
    "retraction",
]

VerificationStatus = Literal["unverified", "preliminary", "confirmed", "official", "retracted"]

DataProvenance = Literal[
    "LIVE",
    "FORECAST",
    "HISTORICAL",
    "CACHED",
    "UNVERIFIED",
    "SYNTHETIC",
]

GeographicPrecision = Literal[
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


class NormalizedEvent(BaseModel):
    """Unified schema representing a validated, normalized crisis event for Nagpur."""

    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:12]}")
    source_id: str = Field(..., description="Adapter identifier, e.g. imd-nagpur, open-meteo, nmc-drainage")
    external_id: str = Field(..., description="Original upstream identifier")
    event_type: EventCategory = Field(..., description="Standardized event category")
    title: str = Field(default="", description="Short human-readable summary")
    description: str = Field(default="", description="Detailed event text or telemetry summary")

    # Geospatial attributes
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    depth_km: float | None = Field(default=None, description="Hypocenter depth for seismic events in km")
    region: str = Field(default="Nagpur, Maharashtra", description="Geographic administrative name")
    zone_id: str = Field(default="Nagpur Operational Region", description="Operational response sector or NMC Zone")
    assigned_zone_id: str | None = Field(default=None, description="Official NMC Zone ID e.g. zone-2-dharampeth")
    assigned_zone_name: str | None = Field(default=None, description="Official human-readable zone name")
    geographic_precision: GeographicPrecision = Field(
        default="approximate",
        description="Exact sensor vs hotspot vs zone vs district-wide precision"
    )
    admin_level: AdminLevel = Field(default="municipal_urban")
    is_nagpur_relevant: bool = Field(default=True, description="True if within Nagpur monitoring boundary or downstream")

    # Temporal attributes
    event_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Observation or ground-truth occurrence timestamp (UTC)",
    )
    ingestion_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Retrieval and pipeline processing timestamp (UTC)",
    )

    # Measurement, provenance and quality metrics
    data_provenance: DataProvenance = Field(
        default="LIVE",
        description="Verifiable source origin: LIVE, FORECAST, HISTORICAL, CACHED, UNVERIFIED, SYNTHETIC"
    )
    severity: float = Field(default=0.5, ge=0.0, le=1.0, description="Normalized severity index (0.0=benign, 1.0=critical)")
    magnitude: float | None = Field(default=None, description="Raw physical measurement value")
    magnitude_unit: str | None = Field(default=None, description="Physical measurement unit (e.g. mm/h, km/h, %, Richter, MW)")
    source_reliability: float = Field(default=0.8, ge=0.0, le=1.0, description="Prior trust score of reporting source")
    confidence: float = Field(default=0.75, ge=0.0, le=1.0, description="Estimated observation confidence")
    data_freshness_seconds: float = Field(default=0.0, ge=0.0, description="Age of observation at ingestion time")
    verification_status: VerificationStatus = Field(default="preliminary")

    # Traceability and topology
    source_url: str | None = Field(default=None, description="Public verification link")
    gateway_id: str | None = Field(default=None, description="Shared gateway or sensor cluster ID for correlation")
    quality_flags: list[str] = Field(default_factory=list, description="Diagnostic data-quality flags")
    payload: dict[str, Any] = Field(default_factory=dict, description="Raw upstream attributes for auditing")

    @field_validator("event_timestamp", "ingestion_timestamp")
    @classmethod
    def ensure_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def to_legacy_dict(self) -> dict[str, Any]:
        """Produce a dictionary compatible with dashboard components."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source_id": self.source_id,
            "external_id": self.external_id,
            "title": self.title,
            "description": self.description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "region": self.region,
            "zone_id": self.zone_id,
            "assigned_zone_id": self.assigned_zone_id,
            "assigned_zone_name": self.assigned_zone_name,
            "geographic_precision": self.geographic_precision,
            "admin_level": self.admin_level,
            "is_nagpur_relevant": self.is_nagpur_relevant,
            "event_timestamp": self.event_timestamp.isoformat(),
            "ingestion_timestamp": self.ingestion_timestamp.isoformat(),
            "data_provenance": self.data_provenance,
            "severity": self.severity,
            "magnitude": self.magnitude,
            "magnitude_unit": self.magnitude_unit,
            "reliability": self.source_reliability,
            "confidence": self.confidence,
            "verification_status": self.verification_status,
            "source_url": self.source_url,
            "gateway_id": self.gateway_id,
            "quality_flags": self.quality_flags,
            "payload": self.payload,
        }
