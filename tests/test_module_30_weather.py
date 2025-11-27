"""
Tests for Module 30: Weather Integration
Tests weather service abstraction and providers
"""

from datetime import date, datetime, timedelta

import pytest
from django.utils import timezone

from core.services.weather import (
    MockWeatherProvider,
    OpenWeatherMapProvider,
    WeatherProvider,
    WeatherService,
    weather_service,
)


@pytest.mark.django_db
class TestMockWeatherProvider:
    """Tests for mock weather provider"""

    def test_mock_provider_returns_data(self):
        """Test mock provider returns weather data"""
        provider = MockWeatherProvider()
        data = provider.get_weather(40.7128, -74.0060)

        assert "temperature" in data
        assert "condition" in data
        assert "humidity" in data
        assert "wind_speed" in data
        assert "description" in data
        assert data["provider"] == "mock"

    def test_mock_provider_data_types(self):
        """Test mock provider returns correct data types"""
        provider = MockWeatherProvider()
        data = provider.get_weather(40.7128, -74.0060)

        assert isinstance(data["temperature"], (int, float))
        assert isinstance(data["condition"], str)
        assert isinstance(data["humidity"], int)
        assert isinstance(data["wind_speed"], (int, float))
        assert isinstance(data["description"], str)

    def test_mock_provider_accepts_date_parameter(self):
        """Test mock provider accepts optional date parameter"""
        provider = MockWeatherProvider()
        date = datetime(2025, 6, 15)
        data = provider.get_weather(40.7128, -74.0060, date=date)

        assert data is not None
        assert "temperature" in data


@pytest.mark.django_db
class TestOpenWeatherMapProvider:
    """Tests for OpenWeatherMap provider"""

    def test_provider_requires_api_key(self):
        """Test provider raises error without API key"""
        provider = OpenWeatherMapProvider(api_key=None)

        with pytest.raises(ValueError, match="API key not configured"):
            provider.get_weather(40.7128, -74.0060)

    def test_provider_with_api_key_returns_data(self):
        """Test provider returns data when API key is provided"""
        # Mock API key for testing
        provider = OpenWeatherMapProvider(api_key="test_key")
        data = provider.get_weather(40.7128, -74.0060)

        assert "temperature" in data
        assert "condition" in data
        assert "humidity" in data
        assert data["provider"] == "openweathermap"

    def test_provider_data_structure(self):
        """Test provider returns expected data structure"""
        provider = OpenWeatherMapProvider(api_key="test_key")
        data = provider.get_weather(40.7128, -74.0060)

        # Check all required fields
        required_fields = ["temperature", "condition", "humidity", "wind_speed", "description", "icon", "provider"]
        for field in required_fields:
            assert field in data


@pytest.mark.django_db
class TestWeatherService:
    """Tests for weather service singleton"""

    def test_service_is_singleton(self):
        """Test WeatherService follows singleton pattern"""
        service1 = WeatherService()
        service2 = WeatherService()

        assert service1 is service2

    def test_service_has_default_provider(self):
        """Test service has mock provider by default"""
        service = WeatherService()
        provider = service.get_provider()

        assert provider is not None
        assert isinstance(provider, MockWeatherProvider)

    def test_service_can_change_provider(self):
        """Test service can switch providers"""
        service = WeatherService()
        new_provider = OpenWeatherMapProvider(api_key="test")

        service.set_provider(new_provider)

        assert service.get_provider() == new_provider

    def test_service_get_weather_delegates_to_provider(self):
        """Test service delegates to configured provider"""
        service = WeatherService()
        service.set_provider(MockWeatherProvider())

        data = service.get_weather(40.7128, -74.0060)

        assert data["provider"] == "mock"

    def test_configure_for_testing(self):
        """Test testing configuration"""
        WeatherService.configure_for_testing()
        service = WeatherService()

        provider = service.get_provider()
        assert isinstance(provider, MockWeatherProvider)

    def test_global_instance_exists(self):
        """Test global weather_service instance is available"""
        from core.services.weather import weather_service

        assert weather_service is not None
        assert isinstance(weather_service, WeatherService)


@pytest.mark.django_db
class TestWeatherServiceIntegration:
    """Integration tests with DailyPlan model"""

    def test_daily_plan_fetch_weather(self):
        """Test DailyPlan.fetch_weather() uses WeatherService"""
        from datetime import date

        from django.contrib.auth.models import User

        from core.models import DailyPlan, Project

        # Configure mock provider
        WeatherService.configure_for_testing()

        # Create test data
        user = User.objects.create_user("testuser", "test@test.com", "pass")
        project = Project.objects.create(
            name="Test Project", address="123 Main St, New York, NY", start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1),
        )

        # Fetch weather
        weather = plan.fetch_weather()

        assert weather is not None
        assert "temperature" in weather
        assert "condition" in weather
        assert plan.weather_data is not None
        assert plan.weather_fetched_at is not None

    def test_daily_plan_weather_without_address(self):
        """Test fetch_weather returns None when project has no address"""
        from datetime import date

        from django.contrib.auth.models import User

        from core.models import DailyPlan, Project

        user = User.objects.create_user("testuser", "test@test.com", "pass")
        project = Project.objects.create(name="Test Project", address="", start_date=date.today())  # No address
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1),
        )

        weather = plan.fetch_weather()

        assert weather is None

    def test_weather_data_persisted_to_database(self):
        """Test weather data is saved to database"""
        from datetime import date

        from django.contrib.auth.models import User

        from core.models import DailyPlan, Project

        WeatherService.configure_for_testing()

        user = User.objects.create_user("testuser", "test@test.com", "pass")
        project = Project.objects.create(name="Test Project", address="123 Main St", start_date=date.today())
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1),
        )

        plan.fetch_weather()
        plan.refresh_from_db()

        assert plan.weather_data is not None
        assert isinstance(plan.weather_data, dict)
        assert plan.weather_fetched_at is not None


@pytest.mark.django_db
class TestWeatherProviderAbstraction:
    """Tests for provider abstraction and extensibility"""

    def test_custom_provider_implementation(self):
        """Test can create custom weather provider"""

        class CustomProvider(WeatherProvider):
            def get_weather(self, latitude, longitude, date=None):
                return {
                    "temperature": 25.0,
                    "condition": "Custom",
                    "humidity": 50,
                    "wind_speed": 10.0,
                    "description": "Custom provider data",
                    "icon": "custom",
                    "provider": "custom",
                }

        service = WeatherService()
        service.set_provider(CustomProvider())

        data = service.get_weather(0, 0)

        assert data["provider"] == "custom"
        assert data["temperature"] == 25.0

    def test_provider_interface_enforcement(self):
        """Test provider must implement get_weather method"""

        class IncompleteProvider(WeatherProvider):
            pass

        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            IncompleteProvider()
