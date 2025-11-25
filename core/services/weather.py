"""
Weather Service for Module 30
Provides abstraction for weather data fetching with multiple providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from datetime import datetime
import os


class WeatherProvider(ABC):
    """Abstract base class for weather providers"""
    
    @abstractmethod
    def get_weather(self, latitude: float, longitude: float, date: Optional[datetime] = None) -> Dict:
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
    
    def get_weather(self, latitude: float, longitude: float, date: Optional[datetime] = None) -> Dict:
        """Returns realistic mock weather data"""
        return {
            'temperature': 22.5,
            'condition': 'Clear',
            'humidity': 65,
            'wind_speed': 12.5,
            'description': 'Clear sky with light breeze',
            'icon': '01d',
            'provider': 'mock',
            'fetched_at': datetime.now().isoformat()
        }


class OpenWeatherMapProvider(WeatherProvider):
    """OpenWeatherMap API provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenWeatherMap provider
        
        Args:
            api_key: API key (defaults to OPENWEATHERMAP_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('OPENWEATHERMAP_API_KEY')
        self.base_url = 'https://api.openweathermap.org/data/2.5'
    
    def get_weather(self, latitude: float, longitude: float, date: Optional[datetime] = None) -> Dict:
        """
        Fetch weather from OpenWeatherMap API
        
        Note: Currently returns mock data. Implement API call when ready.
        TODO: Add requests library call to OpenWeatherMap API
        """
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key not configured")
        
        # TODO: Implement actual API call
        # For now, return mock data with note
        return {
            'temperature': 20.0,
            'condition': 'Partly Cloudy',
            'humidity': 70,
            'wind_speed': 15.0,
            'description': 'Scattered clouds',
            'icon': '02d',
            'provider': 'openweathermap',
            'fetched_at': datetime.now().isoformat(),
            'note': 'Mock data - API integration pending'
        }
        
        # Real implementation would look like:
        # import requests
        # url = f"{self.base_url}/weather"
        # params = {
        #     'lat': latitude,
        #     'lon': longitude,
        #     'appid': self.api_key,
        #     'units': 'metric',
        #     'lang': 'es'
        # }
        # response = requests.get(url, params=params)
        # response.raise_for_status()
        # data = response.json()
        # return {
        #     'temperature': data['main']['temp'],
        #     'condition': data['weather'][0]['main'],
        #     'humidity': data['main']['humidity'],
        #     'wind_speed': data['wind']['speed'] * 3.6,  # m/s to km/h
        #     'description': data['weather'][0]['description'],
        #     'icon': data['weather'][0]['icon'],
        #     'provider': 'openweathermap',
        #     'fetched_at': datetime.now().isoformat()
        # }


class WeatherService:
    """
    Main weather service - manages providers and caching
    Singleton pattern for app-wide configuration
    """
    _instance = None
    _provider: WeatherProvider = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Default to mock provider
            cls._instance._provider = MockWeatherProvider()
        return cls._instance
    
    def set_provider(self, provider: WeatherProvider):
        """Set the weather provider to use"""
        self._provider = provider
    
    def get_provider(self) -> WeatherProvider:
        """Get current weather provider"""
        return self._provider
    
    def get_weather(self, latitude: float, longitude: float, date: Optional[datetime] = None) -> Dict:
        """
        Get weather data using configured provider
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            date: Optional date for forecast/historical
            
        Returns:
            Weather data dict
        """
        if not self._provider:
            raise RuntimeError("Weather provider not configured")
        
        return self._provider.get_weather(latitude, longitude, date)
    
    @classmethod
    def configure_for_production(cls):
        """Configure service for production use with OpenWeatherMap"""
        service = cls()
        api_key = os.getenv('OPENWEATHERMAP_API_KEY')
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
