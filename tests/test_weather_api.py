"""
Tests for Weather API integration (Phase 9)
- Open-Meteo API integration
- WeatherSnapshot creation
- Error handling and fallbacks
"""
import pytest
from unittest.mock import patch, Mock
from django.utils import timezone
from datetime import timedelta
from core.models import Project, WeatherSnapshot
from core.tasks import update_daily_weather_snapshots


@pytest.mark.django_db
class TestWeatherAPI:
    """Test Open-Meteo API integration"""
    
    def test_weather_snapshot_successful_api_call(self, mocker):
        """Test successful weather data fetch from Open-Meteo"""
        # Create test project
        project = Project.objects.create(
            name='Test Weather Project',
            start_date=timezone.now().date()
        )
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'daily': {
                'temperature_2m_max': [25.5],
                'temperature_2m_min': [15.2],
                'precipitation_sum': [2.3],
                'windspeed_10m_max': [18.5],
                'weathercode': [61]  # Slight rain
            }
        }
        mock_response.raise_for_status = Mock()
        
        mock_get = mocker.patch('requests.get', return_value=mock_response)
        
        # Run task
        result = update_daily_weather_snapshots()
        
        # Verify API was called
        assert mock_get.called
        call_args = mock_get.call_args
        assert 'https://api.open-meteo.com' in call_args[0][0]
        
        # Verify snapshot was created
        assert result['created'] == 1
        assert result['errors'] == []
        
        snapshot = WeatherSnapshot.objects.get(project=project)
        assert float(snapshot.temperature_max) == 25.5
        assert float(snapshot.temperature_min) == 15.2
        assert float(snapshot.precipitation_mm) == 2.3
        assert snapshot.conditions_text == 'Slight rain'
        assert snapshot.source == 'open-meteo'
    
    def test_weather_snapshot_api_error_handling(self, mocker):
        """Test graceful handling of API errors"""
        project = Project.objects.create(
            name='Test Error Project',
            start_date=timezone.now().date()
        )
        
        # Mock API error
        import requests
        mock_get = mocker.patch.object(requests, 'get', side_effect=Exception('API timeout'))
        
        # Run task (should not crash)
        result = update_daily_weather_snapshots()
        
        # Verify error was logged
        assert len(result['errors']) > 0
        assert 'Test Error Project' in result['errors'][0]
        
        # Verify no snapshot was created
        assert not WeatherSnapshot.objects.filter(project=project).exists()
    
    def test_weather_snapshot_updates_existing(self, mocker):
        """Test updating existing weather snapshot for same day"""
        project = Project.objects.create(
            name='Update Test Project',
            start_date=timezone.now().date()
        )
        today = timezone.now().date()
        
        # Create existing snapshot
        WeatherSnapshot.objects.create(
            project=project,
            date=today,
            source='open-meteo',
            temperature_max=20.0,
            temperature_min=10.0,
            conditions_text='Clear',
            precipitation_mm=0
        )
        
        # Mock new API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'daily': {
                'temperature_2m_max': [28.0],
                'temperature_2m_min': [18.0],
                'precipitation_sum': [0],
                'windspeed_10m_max': [12.0],
                'weathercode': [0]  # Clear sky
            }
        }
        mock_response.raise_for_status = Mock()
        mocker.patch('requests.get', return_value=mock_response)
        
        # Run task
        result = update_daily_weather_snapshots()
        
        # Verify existing snapshot was updated, not created new
        assert result['created'] == 0
        assert result['updated'] == 1
        
        snapshot = WeatherSnapshot.objects.get(project=project, date=today)
        assert snapshot.temperature_max == 28.0
        assert snapshot.temperature_min == 18.0
    
    def test_weather_codes_mapping(self, mocker):
        """Test WMO weather code to description mapping"""
        project = Project.objects.create(
            name='Weather Code Test',
            start_date=timezone.now().date()
        )
        
        test_cases = [
            (0, 'Clear sky'),
            (2, 'Partly cloudy'),
            (61, 'Slight rain'),
            (95, 'Thunderstorm'),
            (75, 'Heavy snow')
        ]
        
        for weather_code, expected_text in test_cases:
            mock_response = Mock()
            mock_response.json.return_value = {
                'daily': {
                    'temperature_2m_max': [20.0],
                    'temperature_2m_min': [10.0],
                    'precipitation_sum': [0],
                    'windspeed_10m_max': [10.0],
                    'weathercode': [weather_code]
                }
            }
            mock_response.raise_for_status = Mock()
            mocker.patch('requests.get', return_value=mock_response)
            
            # Delete existing snapshot
            WeatherSnapshot.objects.filter(project=project).delete()
            
            # Run task
            update_daily_weather_snapshots()
            
            snapshot = WeatherSnapshot.objects.get(project=project)
            assert snapshot.conditions_text == expected_text
    
    def test_weather_api_only_active_projects(self, mocker):
        """Test that only active projects get weather updates"""
        today = timezone.now().date()
        
        # Active project (no end date)
        active1 = Project.objects.create(
            name='Active 1',
            start_date=today
        )
        
        # Active project (end date in future)
        active2 = Project.objects.create(
            name='Active 2',
            start_date=today,
            end_date=today + timedelta(days=30)
        )
        
        # Completed project (end date in past)
        completed = Project.objects.create(
            name='Completed',
            start_date=today - timedelta(days=60),
            end_date=today - timedelta(days=1)
        )
        
        # Mock API
        mock_response = Mock()
        mock_response.json.return_value = {
            'daily': {
                'temperature_2m_max': [20.0],
                'temperature_2m_min': [10.0],
                'precipitation_sum': [0],
                'windspeed_10m_max': [10.0],
                'weathercode': [0]
            }
        }
        mock_response.raise_for_status = Mock()
        mocker.patch('requests.get', return_value=mock_response)
        
        # Run task
        result = update_daily_weather_snapshots()
        
        # Verify only active projects got weather data
        assert result['created'] == 2  # active1 + active2
        assert WeatherSnapshot.objects.filter(project=active1).exists()
        assert WeatherSnapshot.objects.filter(project=active2).exists()
        assert not WeatherSnapshot.objects.filter(project=completed).exists()
    
    def test_weather_api_parameters(self, mocker):
        """Test that API is called with correct parameters"""
        project = Project.objects.create(
            name='Param Test',
            start_date=timezone.now().date()
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'daily': {
                'temperature_2m_max': [20.0],
                'temperature_2m_min': [10.0],
                'precipitation_sum': [0],
                'windspeed_10m_max': [10.0],
                'weathercode': [0]
            }
        }
        mock_response.raise_for_status = Mock()
        
        mock_get = mocker.patch('requests.get', return_value=mock_response)
        
        # Run task
        update_daily_weather_snapshots()
        
        # Verify parameters
        call_args, call_kwargs = mock_get.call_args
        params = call_kwargs['params']
        
        assert 'latitude' in params
        assert 'longitude' in params
        assert params['forecast_days'] == 1
        assert 'temperature_2m_max' in params['daily']
        assert 'temperature_2m_min' in params['daily']
        assert 'precipitation_sum' in params['daily']
        assert 'windspeed_10m_max' in params['daily']
        assert 'weathercode' in params['daily']
    
    def test_humidity_estimation_logic(self, mocker):
        """Test humidity estimation based on precipitation"""
        project = Project.objects.create(
            name='Humidity Test',
            start_date=timezone.now().date()
        )
        
        test_cases = [
            (0, 50),      # No rain → 50% humidity
            (2.5, 65),    # Light rain → 65% humidity
            (8.0, 80)     # Heavy rain → 80% humidity
        ]
        
        for precipitation, expected_humidity in test_cases:
            mock_response = Mock()
            mock_response.json.return_value = {
                'daily': {
                    'temperature_2m_max': [20.0],
                    'temperature_2m_min': [10.0],
                    'precipitation_sum': [precipitation],
                    'windspeed_10m_max': [10.0],
                    'weathercode': [0]
                }
            }
            mock_response.raise_for_status = Mock()
            mocker.patch('requests.get', return_value=mock_response)
            
            # Delete existing snapshot
            WeatherSnapshot.objects.filter(project=project).delete()
            
            # Run task
            update_daily_weather_snapshots()
            
            snapshot = WeatherSnapshot.objects.get(project=project)
            assert snapshot.humidity_percent == expected_humidity


@pytest.mark.django_db
class TestWeatherSnapshotModel:
    """Test WeatherSnapshot model functionality"""
    
    def test_weather_snapshot_creation(self):
        """Test basic WeatherSnapshot creation"""
        project = Project.objects.create(
            name='Snapshot Test',
            start_date=timezone.now().date()
        )
        
        snapshot = WeatherSnapshot.objects.create(
            project=project,
            date=timezone.now().date(),
            source='open-meteo',
            temperature_max=25.5,
            temperature_min=15.2,
            conditions_text='Partly cloudy',
            precipitation_mm=1.5,
            wind_kph=12.0,
            humidity_percent=60,
            provider_url='https://open-meteo.com'
        )
        
        assert snapshot.project == project
        assert snapshot.temperature_max == 25.5
        assert snapshot.conditions_text == 'Partly cloudy'
    
    def test_weather_snapshot_raw_json_storage(self):
        """Test storing raw API response in JSON field"""
        project = Project.objects.create(
            name='JSON Test',
            start_date=timezone.now().date()
        )
        
        raw_data = {
            'latitude': 37.7749,
            'longitude': -122.4194,
            'weather_code': 61,
            'temperature_max': 22.5
        }
        
        snapshot = WeatherSnapshot.objects.create(
            project=project,
            date=timezone.now().date(),
            source='open-meteo',
            temperature_max=22.5,
            raw_json=raw_data
        )
        
        # Verify JSON field stores and retrieves data
        retrieved = WeatherSnapshot.objects.get(id=snapshot.id)
        assert retrieved.raw_json['latitude'] == 37.7749
        assert retrieved.raw_json['weather_code'] == 61
