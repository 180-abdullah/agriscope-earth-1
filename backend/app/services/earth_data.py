from __future__ import annotations

import csv
import io
import os
import threading
import time
from typing import Any

import httpx


class EarthDataClient:
    """Bounded clients for public Earth-data services with a small TTL cache."""

    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    FLOOD_URL = "https://flood-api.open-meteo.com/v1/flood"
    FIRMS_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

    def __init__(self, timeout_seconds: float = 12.0, ttl_seconds: int = 600) -> None:
        self.timeout_seconds = timeout_seconds
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[float, Any]] = {}
        # A regular lock keeps the cache safe across FastAPI's event loop and
        # Streamlit's rerun-created event loops. No network I/O occurs while
        # the lock is held.
        self._lock = threading.Lock()

    async def _json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        cache_key = f"{url}:{sorted(params.items())}"
        with self._lock:
            hit = self._cache.get(cache_key)
            if hit and hit[0] > time.time():
                return hit[1]
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=False) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
        with self._lock:
            self._cache[cache_key] = (time.time() + self.ttl_seconds, payload)
        return payload

    async def weather(self, latitude: float, longitude: float) -> dict[str, Any]:
        return await self._json(
            self.WEATHER_URL,
            {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,soil_moisture_0_to_7cm,et0_fao_evapotranspiration",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration",
                "forecast_days": 7,
                "timezone": "auto",
            },
        )

    async def flood(self, latitude: float, longitude: float) -> dict[str, Any]:
        return await self._json(
            self.FLOOD_URL,
            {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "river_discharge,river_discharge_mean,river_discharge_max",
                "forecast_days": 7,
            },
        )

    async def fires(self, latitude: float, longitude: float, days: int = 2) -> list[dict[str, Any]]:
        map_key = os.getenv("FIRMS_MAP_KEY", "").strip()
        if not map_key:
            return []
        delta = 0.5
        bbox = f"{longitude-delta},{latitude-delta},{longitude+delta},{latitude+delta}"
        url = f"{self.FIRMS_URL}/{map_key}/VIIRS_SNPP_NRT/{bbox}/{max(1, min(days, 5))}"
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=False) as client:
            response = await client.get(url)
            response.raise_for_status()
        return list(csv.DictReader(io.StringIO(response.text)))


earth_data = EarthDataClient()
