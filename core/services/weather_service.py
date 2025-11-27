"""WeatherService with simple in-memory cache.
Module 30 skeleton: to be replaced by real API integration.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class WeatherData:
    location: str
    temperature_c: float
    condition: str
    fetched_at: float


class WeatherService:
    def __init__(self, ttl_seconds: int = 1800):
        self._cache: dict[str, WeatherData] = {}
        self.ttl = ttl_seconds

    def _simulate_fetch(self, location: str) -> WeatherData:
        # Placeholder: replace with real API call
        conditions = ["Soleado", "Nublado", "Lluvioso", "Ventoso"]
        return WeatherData(
            location=location,
            temperature_c=round(random.uniform(12, 32), 1),
            condition=random.choice(conditions),
            fetched_at=time.time(),
        )

    def get_weather(self, location: str) -> WeatherData:
        existing = self._cache.get(location)
        now = time.time()
        if existing and (now - existing.fetched_at) < self.ttl:
            return existing
        data = self._simulate_fetch(location)
        self._cache[location] = data
        return data

    def serialize(self, data: WeatherData) -> dict[str, Any]:
        return {
            "location": data.location,
            "temperature_c": data.temperature_c,
            "condition": data.condition,
            "fetched_at": data.fetched_at,
        }


# Singleton accessor
_weather_service: WeatherService | None = None


def get_weather_service() -> WeatherService:
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service
