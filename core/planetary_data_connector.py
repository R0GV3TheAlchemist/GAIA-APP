"""planetary_data_connector.py

GAIA's interface to real planetary data sources.
This is how GAIA reads ATLAS — through instrumentation, not metaphor.

Data sources:
  - NASA FIRMS (wildfire detection)
  - OpenWeatherMap (atmospheric state)
  - Copernicus / Sentinel Hub (satellite Earth observation)
  - NOAA (climate and ocean state)
  - Schumann Resonance (ELF electromagnetic field data)

All methods return structured dicts for downstream processing
by PhaseStateMonitor, CollectiveSignalLayer, and BiometricSyncEngine.
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — pull from environment, never hard-code keys
# ---------------------------------------------------------------------------
NASA_FIRMS_KEY = os.getenv("NASA_FIRMS_API_KEY", "")
OWM_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")
COPERNICUS_KEY = os.getenv("COPERNICUS_API_KEY", "")

_BASE_FIRMS = "https://firms.modaps.eosdis.nasa.gov/api"
_BASE_OWM = "https://api.openweathermap.org/data/2.5"
_BASE_COPERNICUS = "https://services.sentinel-hub.com"


class PlanetaryDataConnector:
    """Aggregates real-time planetary data streams for GAIA.

    Instantiate once at runtime and reuse across modules:

        connector = PlanetaryDataConnector()
        fires = connector.get_active_wildfires(area="world", day_range=1)
        weather = connector.get_atmospheric_state(lat=29.42, lon=-98.49)
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self._client = httpx.Client(timeout=timeout)

    # ------------------------------------------------------------------
    # NASA FIRMS — wildfire detection
    # ------------------------------------------------------------------
    def get_active_wildfires(
        self,
        area: str = "world",
        source: str = "VIIRS_NOAA20_NRT",
        day_range: int = 1,
    ) -> dict:
        """Return active fire detections from NASA FIRMS satellite sensors.

        Args:
            area: bounding box as 'lon_min,lat_min,lon_max,lat_max' or 'world'
            source: satellite source (VIIRS_NOAA20_NRT, MODIS_NRT, etc.)
            day_range: number of days back to query (1-10)

        Returns:
            dict with keys: source, timestamp, count, raw_csv
        """
        if not NASA_FIRMS_KEY:
            logger.warning("NASA_FIRMS_API_KEY not set — wildfire data unavailable")
            return {"source": "NASA_FIRMS", "error": "API key not configured"}

        url = f"{_BASE_FIRMS}/area/csv/{NASA_FIRMS_KEY}/{source}/{area}/{day_range}"
        try:
            resp = self._client.get(url)
            resp.raise_for_status()
            lines = resp.text.strip().split("\n")
            return {
                "source": "NASA_FIRMS",
                "satellite": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "day_range": day_range,
                "count": max(0, len(lines) - 1),  # subtract header
                "raw_csv": resp.text,
            }
        except httpx.HTTPError as exc:
            logger.error("FIRMS request failed: %s", exc)
            return {"source": "NASA_FIRMS", "error": str(exc)}

    # ------------------------------------------------------------------
    # OpenWeatherMap — atmospheric state
    # ------------------------------------------------------------------
    def get_atmospheric_state(
        self,
        lat: float,
        lon: float,
        units: str = "metric",
    ) -> dict:
        """Return current atmospheric conditions at a geographic coordinate.

        Args:
            lat: latitude in decimal degrees
            lon: longitude in decimal degrees
            units: 'metric' | 'imperial' | 'standard'

        Returns:
            dict with temp, humidity, pressure, wind, description, timestamp
        """
        if not OWM_KEY:
            logger.warning("OPENWEATHERMAP_API_KEY not set — atmospheric data unavailable")
            return {"source": "OpenWeatherMap", "error": "API key not configured"}

        url = f"{_BASE_OWM}/weather"
        params = {"lat": lat, "lon": lon, "appid": OWM_KEY, "units": units}
        try:
            resp = self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            main = data.get("main", {})
            wind = data.get("wind", {})
            weather = data.get("weather", [{}])[0]
            return {
                "source": "OpenWeatherMap",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "location": data.get("name", ""),
                "lat": lat,
                "lon": lon,
                "temperature_c": main.get("temp"),
                "feels_like_c": main.get("feels_like"),
                "humidity_pct": main.get("humidity"),
                "pressure_hpa": main.get("pressure"),
                "wind_speed_ms": wind.get("speed"),
                "wind_direction_deg": wind.get("deg"),
                "description": weather.get("description", ""),
                "icon": weather.get("icon", ""),
            }
        except httpx.HTTPError as exc:
            logger.error("OWM request failed: %s", exc)
            return {"source": "OpenWeatherMap", "error": str(exc)}

    def get_air_quality(
        self,
        lat: float,
        lon: float,
    ) -> dict:
        """Return current air quality index and pollutant concentrations.

        Returns:
            dict with aqi (1-5 scale), co, no2, o3, pm2_5, pm10
        """
        if not OWM_KEY:
            return {"source": "OpenWeatherMap_AQI", "error": "API key not configured"}

        url = f"{_BASE_OWM}/air_pollution"
        params = {"lat": lat, "lon": lon, "appid": OWM_KEY}
        try:
            resp = self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            item = data.get("list", [{}])[0]
            components = item.get("components", {})
            return {
                "source": "OpenWeatherMap_AQI",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "lat": lat,
                "lon": lon,
                "aqi": item.get("main", {}).get("aqi"),  # 1=Good .. 5=VeryPoor
                "co_ugm3": components.get("co"),
                "no2_ugm3": components.get("no2"),
                "o3_ugm3": components.get("o3"),
                "pm2_5_ugm3": components.get("pm2_5"),
                "pm10_ugm3": components.get("pm10"),
            }
        except httpx.HTTPError as exc:
            logger.error("OWM AQI request failed: %s", exc)
            return {"source": "OpenWeatherMap_AQI", "error": str(exc)}

    # ------------------------------------------------------------------
    # Copernicus / Sentinel Hub — satellite Earth observation
    # ------------------------------------------------------------------
    def get_sentinel_token(self) -> Optional[str]:
        """Authenticate with Copernicus and return a bearer token."""
        if not COPERNICUS_KEY:
            logger.warning("COPERNICUS_API_KEY not set")
            return None

        client_id, client_secret = (COPERNICUS_KEY.split(":", 1) + [""])[:2]
        auth_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        try:
            resp = self._client.post(
                auth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            return resp.json().get("access_token")
        except httpx.HTTPError as exc:
            logger.error("Copernicus auth failed: %s", exc)
            return None

    def search_sentinel_scenes(
        self,
        bbox: tuple[float, float, float, float],
        date_from: str,
        date_to: str,
        collection: str = "SENTINEL-2",
        max_cloud_cover: int = 30,
    ) -> dict:
        """Search for available Sentinel satellite scenes over a bounding box.

        Args:
            bbox: (lon_min, lat_min, lon_max, lat_max)
            date_from: ISO date string e.g. '2026-04-01'
            date_to: ISO date string e.g. '2026-04-14'
            collection: satellite collection name
            max_cloud_cover: maximum cloud cover percentage (0-100)

        Returns:
            dict with scene count and feature list
        """
        token = self.get_sentinel_token()
        if not token:
            return {"source": "Copernicus", "error": "Authentication failed"}

        search_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
        lon_min, lat_min, lon_max, lat_max = bbox
        footprint = (
            f"POLYGON(({lon_min} {lat_min},{lon_max} {lat_min},"
            f"{lon_max} {lat_max},{lon_min} {lat_max},{lon_min} {lat_min}))"
        )
        filter_str = (
            f"Collection/Name eq '{collection}' and "
            f"OData.CSC.Intersects(area=geography'SRID=4326;{footprint}') and "
            f"ContentDate/Start gt {date_from}T00:00:00.000Z and "
            f"ContentDate/Start lt {date_to}T23:59:59.999Z and "
            f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' "
            f"and att/OData.CSC.DoubleAttribute/Value lt {max_cloud_cover})"
        )
        params = {"$filter": filter_str, "$top": 20, "$orderby": "ContentDate/Start desc"}
        try:
            resp = self._client.get(
                search_url,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()
            features = data.get("value", [])
            return {
                "source": "Copernicus",
                "collection": collection,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "scene_count": len(features),
                "scenes": [
                    {
                        "id": f.get("Id"),
                        "name": f.get("Name"),
                        "date": f.get("ContentDate", {}).get("Start"),
                        "size_mb": round(f.get("ContentLength", 0) / 1_048_576, 1),
                    }
                    for f in features
                ],
            }
        except httpx.HTTPError as exc:
            logger.error("Copernicus search failed: %s", exc)
            return {"source": "Copernicus", "error": str(exc)}

    # ------------------------------------------------------------------
    # Composite — planetary health snapshot
    # ------------------------------------------------------------------
    def get_planetary_health_snapshot(
        self,
        lat: float = 0.0,
        lon: float = 0.0,
    ) -> dict:
        """Return a composite planetary health reading at a given coordinate.

        Aggregates atmospheric state, air quality, and active wildfire count
        into a single structured payload for PhaseStateMonitor consumption.

        Args:
            lat: focal latitude (defaults to equator)
            lon: focal longitude (defaults to prime meridian)

        Returns:
            dict with atmospheric, air_quality, wildfire, and timestamp keys
        """
        atmosphere = self.get_atmospheric_state(lat, lon)
        air_quality = self.get_air_quality(lat, lon)
        wildfires = self.get_active_wildfires()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "focal_point": {"lat": lat, "lon": lon},
            "atmospheric": atmosphere,
            "air_quality": air_quality,
            "wildfires": {
                "active_detection_count": wildfires.get("count", None),
                "source": wildfires.get("source"),
                "error": wildfires.get("error"),
            },
        }

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "PlanetaryDataConnector":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
