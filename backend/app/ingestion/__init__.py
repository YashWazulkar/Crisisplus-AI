"""Ingestion Package for CrisisPulse AI: Nagpur Operational Platform."""

from .base import BaseAdapter
from .open_meteo import OpenMeteoAdapter
from .imd_adapter import IMDAdapter
from .drainage_provider import NagpurDrainageWaterloggingProvider
from .hospital_provider import HospitalDataProvider
from .traffic_provider import NagpurTrafficIncidentProvider
from .nasa_firms import NASAFIRMSAdapter
from .usgs_earthquake import USGSEarthquakeAdapter
from .gdacs import GDACSAdapter
from .manager import IngestionManager
