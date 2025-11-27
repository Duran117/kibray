import pytest
from django.utils import timezone


@pytest.mark.django_db
def test_weather_service_cache_and_force_refresh():
    from core.services.weather import MockWeatherProvider, WeatherService, weather_service

    # Ensure testing provider
    WeatherService.configure_for_testing()

    first = weather_service.get_weather(40.712776, -74.005974)
    second = weather_service.get_weather(40.712776, -74.005974)
    assert first["fetched_at"] == second["fetched_at"], "Second call should hit cache"
    assert second["stale"] is False
    # Force refresh should produce different fetched_at
    refreshed = weather_service.get_weather(40.712776, -74.005974, force_refresh=True)
    assert refreshed["fetched_at"] != first["fetched_at"]
    assert refreshed["fallback"] is False


@pytest.mark.django_db
def test_weather_service_circuit_breaker_fallback():
    from core.services.weather import WeatherService, weather_service

    class FailingProvider:
        def __init__(self):
            self.calls = 0

        def get_weather(self, lat, lon, date=None):
            self.calls += 1
            raise RuntimeError("Provider failure")

    # Prime cache with working provider
    WeatherService.configure_for_testing()
    ok = weather_service.get_weather(10.0, 20.0)
    assert ok["fallback"] is False
    # Switch to failing provider
    weather_service.set_provider(FailingProvider())
    # Cause multiple failures until circuit opens
    for _ in range(weather_service.CIRCUIT_THRESHOLD):
        try:
            weather_service.get_weather(10.0, 20.0, force_refresh=True)
        except RuntimeError:
            pass
    # Now circuit should be open; call returns cached fallback
    result = weather_service.get_weather(10.0, 20.0)
    assert result["fallback"] is True
    assert "stale" in result
