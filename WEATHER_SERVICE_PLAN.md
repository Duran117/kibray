# Weather Service Plan (Module 30)

## Objective
Provide reliable, cached weather data (current + short forecast) to enrich DailyPlan and scheduling decisions without incurring excessive external API calls.

## Functional Requirements
- Fetch current weather and next 24h forecast for project coordinates.
- Auto-refresh stale data (>= 60 minutes old) when DailyPlan.fetch_weather() is invoked.
- Provide graceful fallback if provider unreachable (return last known + flag).
- Support multiple providers (primary + secondary) with pluggable strategy.

## Non-Functional
- Cache layer with TTL 60m, per (lat,lon) rounded to 3 decimals (~100m precision).
- Rate limiting: max 100 external calls/hour (aggregate) – enforce via token bucket.
- Resilience: circuit breaker after 5 consecutive failures (open 10 minutes).
- Observability: structured logs (provider, latency ms, hit/miss, fallback used).

## Data Shape
```json
{
  "source": "openmeteo",
  "fetched_at": "2025-11-26T03:40:00Z",
  "location": {"lat": 40.7128, "lon": -74.006},
  "current": {"temp_c": 12.4, "condition": "Cloudy", "humidity": 68, "wind_kph": 9.2},
  "forecast_hours": [
    {"hour": "2025-11-26T04:00:00Z", "temp_c": 12.0, "condition": "Cloudy"},
    {"hour": "2025-11-26T05:00:00Z", "temp_c": 11.8, "condition": "Cloudy"}
  ],
  "stale": false,
  "fallback": false
}
```

## Interface Contract
WeatherService.get_weather(lat: float, lon: float, force_refresh: bool=False) -> dict
- Inputs: coordinates (rounded internally), optional force_refresh bypassing TTL.
- Outputs: weather dict; sets `stale=True` if returned data older than TTL and provider unreachable.
- Errors: raises WeatherProviderError only if no cached data exists and provider fails.

## Edge Cases
- Naive coordinates: normalize rounding & clamp valid ranges.
- Provider partial response (missing humidity): fill with None and log warning.
- High frequency bursts: throttle and serve cache.
- Circuit open: skip provider call, serve cache with `fallback=True`.

## Architecture
- weather_service.py exposes singleton `weather_service`.
- Provider adapters: `providers/openmeteo.py`, `providers/backup_noaa.py` implementing `fetch(lat, lon)`.
- Cache: in-memory dict + optional Redis backend (feature flag USE_REDIS_WEATHER_CACHE).
- Circuit breaker utility in `core/services/utils/circuit.py`.

## Pseudocode
```python
class WeatherService:
    def __init__(self, primary, secondary=None, cache=None, limiter=None, breaker=None):
        ...
    def get_weather(self, lat, lon, force_refresh=False):
        key = self._cache_key(lat, lon)
        data = self.cache.get(key)
        if data and not force_refresh and not self._is_stale(data):
            return {**data, 'stale': False, 'fallback': False}
        if self.breaker.open():
            if data:
                return {**data, 'stale': True, 'fallback': True}
            raise WeatherProviderError('Circuit open and no cache')
        if not self.limiter.allow():
            if data:
                return {**data, 'stale': True, 'fallback': True}
            raise WeatherProviderError('Rate limited and no cache')
        try:
            fresh = self.primary.fetch(lat, lon)
        except Exception:
            self.breaker.record_failure()
            if self.secondary:
                try:
                    fresh = self.secondary.fetch(lat, lon)
                except Exception:
                    fresh = None
            else:
                fresh = None
        if fresh:
            self.breaker.record_success()
            payload = self._normalize(fresh, lat, lon)
            self.cache.set(key, payload)
            return {**payload, 'stale': False, 'fallback': False}
        if data:
            return {**data, 'stale': True, 'fallback': True}
        raise WeatherProviderError('No provider data and cache miss')
```

## Testing Strategy
- Unit: cache hit, stale fallback, circuit open scenario, rate limit.
- Integration: mock provider responses, failure chains.
- Performance: simulate 500 calls/hour verifying limiter.

## Next Implementation Steps
1. Implement circuit breaker utility.
2. Implement simple in-memory cache with TTL metadata.
3. Implement primary provider adapter (Open-Meteo free endpoint).
4. Wire weather_service singleton and use in DailyPlan.fetch_weather.
5. Add tests.
6. Optional: Redis backend toggle.
