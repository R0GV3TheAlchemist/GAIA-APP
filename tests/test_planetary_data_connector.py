"""Tests for PlanetaryDataConnector.

These tests mock all HTTP calls — no live API keys required to run the suite.
"""

from unittest.mock import MagicMock, patch
import pytest

from core.planetary_data_connector import PlanetaryDataConnector


@pytest.fixture
def connector():
    return PlanetaryDataConnector()


class TestGetAtmosphericState:
    def test_returns_structured_dict_on_success(self, connector):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "San Antonio",
            "main": {"temp": 28.0, "feels_like": 30.0, "humidity": 65, "pressure": 1012},
            "wind": {"speed": 4.5, "deg": 180},
            "weather": [{"description": "clear sky", "icon": "01d"}],
        }
        mock_response.raise_for_status = MagicMock()

        with patch.dict("os.environ", {"OPENWEATHERMAP_API_KEY": "test-key"}):
            with patch("httpx.Client.get", return_value=mock_response):
                result = connector.get_atmospheric_state(lat=29.42, lon=-98.49)

        assert result["source"] == "OpenWeatherMap"
        assert result["temperature_c"] == 28.0
        assert result["humidity_pct"] == 65
        assert result["location"] == "San Antonio"

    def test_returns_error_when_key_missing(self, connector):
        with patch.dict("os.environ", {"OPENWEATHERMAP_API_KEY": ""}, clear=False):
            # Temporarily clear the module-level key
            import core.planetary_data_connector as pdc
            original = pdc.OWM_KEY
            pdc.OWM_KEY = ""
            result = connector.get_atmospheric_state(lat=0.0, lon=0.0)
            pdc.OWM_KEY = original

        assert "error" in result


class TestGetActiveWildfires:
    def test_returns_fire_count_on_success(self, connector):
        csv_data = "latitude,longitude,brightness\n29.4,98.5,320.1\n30.1,97.2,315.8\n"
        mock_response = MagicMock()
        mock_response.text = csv_data
        mock_response.raise_for_status = MagicMock()

        with patch("core.planetary_data_connector.NASA_FIRMS_KEY", "test-key"):
            with patch("httpx.Client.get", return_value=mock_response):
                result = connector.get_active_wildfires()

        assert result["source"] == "NASA_FIRMS"
        assert result["count"] == 2  # 3 lines minus header

    def test_returns_error_when_key_missing(self, connector):
        import core.planetary_data_connector as pdc
        original = pdc.NASA_FIRMS_KEY
        pdc.NASA_FIRMS_KEY = ""
        result = connector.get_active_wildfires()
        pdc.NASA_FIRMS_KEY = original
        assert "error" in result


class TestPlanetaryHealthSnapshot:
    def test_snapshot_aggregates_all_sources(self, connector):
        connector.get_atmospheric_state = MagicMock(return_value={"source": "OpenWeatherMap", "temperature_c": 25.0})
        connector.get_air_quality = MagicMock(return_value={"source": "OpenWeatherMap_AQI", "aqi": 2})
        connector.get_active_wildfires = MagicMock(return_value={"source": "NASA_FIRMS", "count": 47})

        result = connector.get_planetary_health_snapshot(lat=29.42, lon=-98.49)

        assert "atmospheric" in result
        assert "air_quality" in result
        assert result["wildfires"]["active_detection_count"] == 47
        assert result["focal_point"]["lat"] == 29.42
