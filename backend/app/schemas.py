"""CrisisPulse Event Schemas: Nagpur Operational Edition."""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator
import uuid

from .normalization.schema import (
    NormalizedEvent,
    EventCategory,
    VerificationStatus,
    DataProvenance,
    GeographicPrecision,
    AdminLevel,
)
from .geography.nagpur_registry import NAGPUR_CENTER_LAT, NAGPUR_CENTER_LON

EventType = Literal[
    "rainfall", "water_level", "traffic_speed", "road_flooding",
    "ambulance_delay", "hospital_demand", "drainage_overflow", "sensor_failure",
    "gateway_failure", "citizen_report", "power_outage", "source_recovered",
    "wind_gust", "severe_weather", "temperature_anomaly", "earthquake", "wildfire", "flood", "cyclone",
    "retraction"
]

class Event(BaseModel):
    """Backward-compatible event schema supporting synthetic simulator and legacy engine."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    source_id: str
    event_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ingestion_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    zone_id: str = "Nagpur Central Zone"
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    reliability: float = Field(default=0.8, ge=0.0, le=1.0)
    gateway_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    quality_flags: list[str] = Field(default_factory=list)

    # Spatial attributes
    latitude: float | None = None
    longitude: float | None = None
    region: str | None = None
    title: str | None = None
    description: str | None = None
    magnitude: float | None = None
    magnitude_unit: str | None = None
    source_url: str | None = None
    confidence: float = 0.75
    verification_status: str = "preliminary"
    data_provenance: DataProvenance = "LIVE"
    geographic_precision: GeographicPrecision = "approximate"
    admin_level: AdminLevel = "municipal_urban"

    @field_validator("event_timestamp", "ingestion_timestamp")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def to_normalized(self) -> NormalizedEvent:
        """Convert a legacy event to a NormalizedEvent."""
        lat = self.latitude if self.latitude is not None else NAGPUR_CENTER_LAT
        lon = self.longitude if self.longitude is not None else NAGPUR_CENTER_LON
        return NormalizedEvent(
            event_id=self.event_id,
            source_id=self.source_id,
            external_id=self.payload.get("external_id", self.event_id),
            event_type=self.event_type,
            title=self.title or f"{self.event_type.replace('_', ' ').title()} in {self.zone_id}",
            description=self.description or f"Observed {self.event_type} event with severity {self.severity:.2f}",
            latitude=lat,
            longitude=lon,
            region=self.region or "Nagpur, Maharashtra",
            zone_id=self.zone_id,
            event_timestamp=self.event_timestamp,
            ingestion_timestamp=self.ingestion_timestamp,
            severity=self.severity,
            magnitude=self.magnitude,
            magnitude_unit=self.magnitude_unit,
            source_reliability=self.reliability,
            confidence=self.confidence,
            data_provenance=self.data_provenance,
            geographic_precision=self.geographic_precision,
            admin_level=self.admin_level,
            verification_status="preliminary" if self.verification_status not in ("unverified", "preliminary", "confirmed", "official") else self.verification_status,  # type: ignore
            source_url=self.source_url,
            gateway_id=self.gateway_id,
            quality_flags=self.quality_flags,
            payload=self.payload,
        )
