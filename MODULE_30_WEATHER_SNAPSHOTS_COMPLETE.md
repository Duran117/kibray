# Module 30: Weather Snapshots — Complete

Daily weather is cached per project and date to support planning and analytics. This module provides a Weather service abstraction, a `WeatherSnapshot` model, API endpoints, and helpers to fetch or refresh weather data.

## What’s included

- Model: `WeatherSnapshot` (unique per project+date+source)
- Service: `core.services.weather` with provider abstraction and `get_or_create_snapshot()`
- Serializer: `WeatherSnapshotSerializer` with `is_stale` flag
- ViewSet: `WeatherSnapshotViewSet` (read‑only) with listing, filtering, ordering, and `by_project_date` action
- Routes: `/api/weather-snapshots/` registered in `core/api/urls.py`

## Model overview

Fields: `project`, `date`, `source`, `temperature_max`, `temperature_min`, `conditions_text`, `precipitation_mm`, `wind_kph`, `humidity_percent`, `raw_json`, `fetched_at`, `provider_url`, `latitude`, `longitude`.

- `unique_together = (project, date, source)`
- `ordering = ['-date']`
- `is_stale(ttl_hours=6)`: true if snapshot older than TTL hours

See: `core/models.py` (class `WeatherSnapshot`).

## Service overview

- `WeatherProvider` (abstract) with `get_weather(lat, lon, date)`
- Providers:
  - `MockWeatherProvider` (default for tests/dev)
  - `OpenWeatherMapProvider` (skeleton; replace mock with real call when adding API key)
- `WeatherService`
  - Singleton; configure with `configure_for_production()` or `configure_for_testing()`
  - `get_weather(lat, lon, date=None)` delegates to current provider
- Helper: `get_or_create_snapshot(project, lat, lon, date=None)`
  - Reuses fresh snapshot; refreshes if `is_stale()`

See: `core/services/weather.py`.

## API endpoints

- List: GET `/api/v1/weather-snapshots/?project=<id>&source=<name>&ordering=-date`
- Retrieve: GET `/api/v1/weather-snapshots/{id}/`
- Action: GET `/api/v1/weather-snapshots/by_project_date/?project_id=<id>&date=YYYY-MM-DD`

Permissions: `IsAuthenticated`

Filtering: `project`, `date`, `source`
Ordering: `date`, `fetched_at` (default `-date`)

### Example: list snapshots

GET `/api/v1/weather-snapshots/?project=12`

Response (paginated):
{
  "count": 3,
  "results": [
    {
      "id": 41,
      "project": 12,
      "date": "2025-11-25",
      "source": "mock",
      "temperature_max": "22.50",
      "temperature_min": "22.50",
      "conditions_text": "Clear sky with light breeze",
      "humidity_percent": 65,
      "wind_kph": "12.50",
      "fetched_at": "2025-11-25T01:23:45Z",
      "is_stale": false,
      "latitude": "40.71280",
      "longitude": "-74.00600"
    }
  ]
}

### Example: by project and date

GET `/api/v1/weather-snapshots/by_project_date/?project_id=12&date=2025-11-25`

- 200: returns matching snapshot
- 404: when no snapshot exists for that date
- 400: when missing required query params

## Integration with Daily Plans

- `DailyPlan.fetch_weather()` uses `weather_service.get_weather(lat, lon)` and stores `weather_data` inline in the plan for quick access.
- For durable analytics and caching, prefer `get_or_create_snapshot()` and the `WeatherSnapshot` model.

## Configuration

- Default provider is mock (no external calls). In production, set `OPENWEATHERMAP_API_KEY` env var and call `WeatherService.configure_for_production()` (e.g., at startup) to switch to the OpenWeatherMap provider.

## Tests

Functional tests are included under `tests/test_phase1_api.py` and `tests/test_phase1_features.py`:
- API: list, filter, and `by_project_date` action
- Model: creation, TTL staleness, and refresh behavior

No database migrations are required beyond what’s already present in this repository.
