"""
Weather Service for Module 30
Provides abstraction for weather data fetching with multiple providers
"""

from abc import ABC, abstractmethod
from datetime import datetime
import os
from typing import Any

from django.utils import timezone

from core.models import Project, WeatherSnapshot


class WeatherProvider(ABC):
    """Abstract base class for weather providers"""

    @abstractmethod
    def get_weather(self, latitude: float, longitude: float, date: datetime | None = None) -> dict:
        """
        Fetch weather data for a location

        Args:
            latitude: Location latitude
            longitude: Location longitude
            date: Optional date for forecast/historical data

        Returns:
            Dict with weather data: {
                'temperature': float,  # in Celsius
                'condition': str,      # e.g. 'Clear', 'Rain', 'Cloudy'
                'humidity': int,       # percentage
                'wind_speed': float,   # km/h
                'description': str,    # human-readable description
                'icon': str,          # weather icon code
            }
        """
        pass


class MockWeatherProvider(WeatherProvider):
    """Mock provider for testing - returns fake data"""

    def get_weather(self, latitude: float, longitude: float, date: datetime | None = None) -> dict:
        """Returns realistic mock weather data"""
        return {
            "temperature": 22.5,
            "condition": "Clear",
            "humidity": 65,
            "wind_speed": 12.5,
            "description": "Clear sky with light breeze",
            "icon": "01d",
            "provider": "mock",
            "fetched_at": datetime.now().isoformat(),
        }


class OpenWeatherMapProvider(WeatherProvider):
    """OpenWeatherMap API provider"""

    def __init__(self, api_key: str | None = None):
        """
        Initialize OpenWeatherMap provider

        Args:
            api_key: API key (defaults to OPENWEATHERMAP_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENWEATHERMAP_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_weather(self, latitude: float, longitude: float, date: datetime | None = None) -> dict:
        """
        Fetch weather from OpenWeatherMap API

        Implements robust error handling with fallback to mock data.
        """
        import logging

        import requests

        logger = logging.getLogger(__name__)

        # Fallback mock data
        mock_fallback = {
            "temperature": 20.0,
            "condition": "Partly Cloudy",
            "humidity": 70,
            "wind_speed": 15.0,
            "description": "Scattered clouds",
            "icon": "02d",
            "provider": "openweathermap_mock",
            "fetched_at": datetime.now().isoformat(),
        }

        # Check API key
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured. Using fallback mock data.")
            return mock_fallback

        # Build request
        url = f"{self.base_url}/weather"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
            "lang": "es",
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Map OpenWeatherMap response to our format
            return {
                "temperature": data["main"]["temp"],
                "condition": data["weather"][0]["main"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"] * 3.6,  # m/s to km/h
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
                "provider": "openweathermap",
                "fetched_at": datetime.now().isoformat(),
            }

        except requests.exceptions.Timeout:
            logger.error(f"OpenWeatherMap API timeout for lat={latitude}, lon={longitude}. Using fallback.")
            return mock_fallback
        except requests.exceptions.HTTPError as e:
            logger.error(f"OpenWeatherMap HTTP error {e.response.status_code}: {e}. Using fallback.")
            return mock_fallback
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenWeatherMap request failed: {e}. Using fallback.")
            return mock_fallback
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"OpenWeatherMap response parsing error: {e}. Using fallback.")
            return mock_fallback
        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}. Using fallback.")
            return mock_fallback


class WeatherService:
    """Weather service with in-memory cache, rate limiting y circuit breaker.

    Características clave:
    - Cache TTL (por lat/lon redondeado a 3 decimales)
    - Rate limit simple (token bucket light) para evitar exceso de llamadas externas
    - Circuit breaker después de N fallos consecutivos
    - Fallback a datos cache si proveedor falla o circuito abierto
    """

    _instance = None
    _provider: WeatherProvider = None

    # Configuración
    CACHE_TTL_SECONDS = 3600  # 60 min
    MAX_CALLS_PER_HOUR = 100
    CIRCUIT_THRESHOLD = 5
    CIRCUIT_COOLDOWN_SECONDS = 600

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            inst = cls._instance
            inst._provider = MockWeatherProvider()
            inst._cache = {}
            inst._hour_window_start = timezone.now()
            inst._calls_in_window = 0
            inst._failure_count = 0
            inst._circuit_opened_at = None
        return cls._instance

    # -----------------
    # Provider management
    # -----------------
    def set_provider(self, provider: WeatherProvider):
        self._provider = provider

    def get_provider(self) -> WeatherProvider:
        return self._provider

    # -----------------
    # Internals
    # -----------------
    def _cache_key(self, lat: float, lon: float) -> str:
        return f"{round(lat,3)}:{round(lon,3)}"

    def _is_stale(self, payload: dict[str, Any]) -> bool:
        fetched_at_str = payload.get("fetched_at")
        if not fetched_at_str:
            return True
        try:
            fetched_at = datetime.fromisoformat(fetched_at_str.replace("Z", ""))
        except Exception:
            return True
        return (timezone.now() - fetched_at).total_seconds() > self.CACHE_TTL_SECONDS

    def _rate_limit_allow(self) -> bool:
        now = timezone.now()
        if (now - self._hour_window_start).total_seconds() >= 3600:
            self._hour_window_start = now
            self._calls_in_window = 0
        if self._calls_in_window < self.MAX_CALLS_PER_HOUR:
            self._calls_in_window += 1
            return True
        return False

    def _circuit_open(self) -> bool:
        if self._circuit_opened_at is None:
            return False
        # Si cooldown ya pasó, cerrar circuito
        if (timezone.now() - self._circuit_opened_at).total_seconds() > self.CIRCUIT_COOLDOWN_SECONDS:
            self._circuit_opened_at = None
            self._failure_count = 0
            return False
        return True

    def _record_failure(self):
        self._failure_count += 1
        if self._failure_count >= self.CIRCUIT_THRESHOLD and not self._circuit_open():
            self._circuit_opened_at = timezone.now()

    def _record_success(self):
        self._failure_count = 0
        self._circuit_opened_at = None

    def _normalize(self, raw: dict[str, Any], lat: float, lon: float) -> dict[str, Any]:
        # Asegurar llaves requeridas por snapshot logic
        now_iso = timezone.now().isoformat()
        return {
            "temperature": raw.get("temperature")
            or raw.get("temp_c")
            or raw.get("temperature_c")
            or raw.get("temperature")
            or 0.0,
            "condition": raw.get("condition") or raw.get("weather") or raw.get("description") or "Unknown",
            "humidity": raw.get("humidity", 0),
            "wind_speed": raw.get("wind_speed", raw.get("wind_kph", 0.0)),
            "description": raw.get("description") or raw.get("condition") or "N/A",
            "icon": raw.get("icon"),
            "provider": raw.get("provider", "mock"),
            "fetched_at": now_iso,
            "lat": lat,
            "lon": lon,
        }

    # -----------------
    # Public API
    # -----------------
    def get_weather(
        self, latitude: float, longitude: float, date: datetime | None = None, force_refresh: bool = False
    ) -> dict[str, Any]:
        if not self._provider:
            raise RuntimeError("Weather provider not configured")
        key = self._cache_key(latitude, longitude)
        cached = self._cache.get(key)

        # Circuit open -> devolver cache si existe
        if self._circuit_open():
            if cached:
                return {**cached, "stale": self._is_stale(cached), "fallback": True}
            raise RuntimeError("Weather circuit open y sin datos cache disponibles")

        # Cache válido y no force_refresh
        if cached and not force_refresh and not self._is_stale(cached):
            return {**cached, "stale": False, "fallback": False}

        # Rate limit
        if not self._rate_limit_allow():
            if cached:
                return {**cached, "stale": self._is_stale(cached), "fallback": True, "rate_limited": True}
            raise RuntimeError("Weather rate limit excedido y sin cache")

        # Llamar proveedor
        try:
            raw = self._provider.get_weather(latitude, longitude, date)
            normalized = self._normalize(raw, latitude, longitude)
            self._cache[key] = normalized
            self._record_success()
            return {**normalized, "stale": False, "fallback": False}
        except Exception as e:
            self._record_failure()
            if cached:
                return {**cached, "stale": self._is_stale(cached), "fallback": True, "error": str(e)}
            raise

    @classmethod
    def configure_for_production(cls):
        """Configure service for production use with OpenWeatherMap"""
        service = cls()
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if api_key:
            service.set_provider(OpenWeatherMapProvider(api_key))
        else:
            # Fallback to mock if no API key
            service.set_provider(MockWeatherProvider())

    @classmethod
    def configure_for_testing(cls):
        """Configure service for testing with mock provider"""
        service = cls()
        service.set_provider(MockWeatherProvider())


# Global instance
weather_service = WeatherService()


# --- Snapshot helpers ---
def _safe_get(data: Any, key: str, default: Any = None, caster=None):
    """Safely get a value from possibly mocked/mapping-like data and cast it.
    Ensures primitives are stored in the DB even if tests patch with MagicMock.
    """
    val = None
    try:
        # Support mapping-like or dict
        val = data.get(key, default) if hasattr(data, "get") or isinstance(data, dict) else default
    except Exception:
        val = default
    # Apply caster if provided to coerce MagicMock/expressions
    if caster is not None:
        try:
            return caster(val)
        except Exception:
            return caster(default)
    return val


def get_or_create_snapshot(
    project: Project, latitude: float, longitude: float, date: datetime | None = None
) -> WeatherSnapshot:
    """Obtiene o crea un WeatherSnapshot para (project, date). Usa provider configurado.
    Refresca si snapshot está obsoleto (>6h) según lógica `is_stale()`."""
    target_date = (date or timezone.now()).date()
    snap = WeatherSnapshot.objects.filter(project=project, date=target_date, source="openweathermap").first()
    if snap and not snap.is_stale():
        return snap
    # Fallback: if there is a very recent snapshot (within TTL), reuse it even if date differs
    recent = WeatherSnapshot.objects.filter(project=project, source="openweathermap").order_by("-fetched_at").first()
    if recent and not recent.is_stale():
        return recent

    data = weather_service.get_weather(latitude=latitude, longitude=longitude, date=date)
    if snap is None:
        snap = WeatherSnapshot(
            project=project, date=target_date, source=_safe_get(data, "provider", "openweathermap", caster=str)
        )
    # Coerce values to primitives to avoid MagicMock insertions
    snap.temperature_max = _safe_get(data, "temperature", None, caster=lambda v: float(v) if v is not None else None)
    snap.temperature_min = _safe_get(
        data, "temperature", None, caster=lambda v: float(v) if v is not None else None
    )  # hasta tener rango real
    # Prefer description, fallback to condition
    desc = _safe_get(data, "description", None, caster=str)
    if not desc:
        desc = _safe_get(data, "condition", "", caster=str)
    snap.conditions_text = desc or ""
    snap.humidity_percent = _safe_get(data, "humidity", None, caster=lambda v: int(v) if v is not None else None)
    snap.wind_kph = _safe_get(data, "wind_speed", None, caster=lambda v: float(v) if v is not None else None)
    # raw_json must be JSON-serializable (dict)
    snap.raw_json = data if isinstance(data, dict) else {"value": str(data)}
    snap.provider_url = "https://api.openweathermap.org/data/2.5"
    snap.latitude = latitude
    snap.longitude = longitude
    snap.fetched_at = timezone.now()
    snap.save()
    return snap


__all__ = ["weather_service", "WeatherService", "get_or_create_snapshot", "WeatherSnapshot"]
