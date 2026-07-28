from __future__ import annotations

import msgspec
import pytest

from weather.models import Forecast


PAYLOAD = {
    'dt': 1_753_660_800,
    'main': {
        'humidity': 55,
        'pressure': 1013,
        'temp': 21.5,
        'temp_max': 24.0,
        'temp_min': 18.0,
    },
    'name': 'Winnipeg',
    'sys': {'country': 'CA'},
    'weather': [{'description': 'light rain', 'main': 'rain'}],
    'wind': {'speed': 10.0},
}


@pytest.fixture
def forecast() -> Forecast:
    return msgspec.convert(PAYLOAD, type=Forecast)


def test_forecast_renames_wire_fields(forecast: Forecast) -> None:
    assert forecast.main.temperature == 21.5
    assert forecast.main.temperature_max == 24.0
    assert forecast.main.temperature_min == 18.0
    assert forecast.system.country == 'CA'
    assert forecast.timestamp == 1_753_660_800


def test_forecast_ignores_unknown_fields() -> None:
    payload = {**PAYLOAD, 'visibility': 10_000}

    result = msgspec.convert(payload, type=Forecast)
    assert result.city == 'Winnipeg'


def test_forecast_city(forecast: Forecast) -> None:
    assert forecast.city == 'Winnipeg'


def test_forecast_country(forecast: Forecast) -> None:
    assert forecast.country == 'CA'


def test_forecast_celsius(forecast: Forecast) -> None:
    assert forecast.celsius == 21.5
    assert forecast.celsius_high == 24.0
    assert forecast.celsius_low == 18.0


def test_forecast_fahrenheit(forecast: Forecast) -> None:
    assert forecast.fahrenheit == pytest.approx(70.7)
    assert forecast.fahrenheit_high == pytest.approx(75.2)
    assert forecast.fahrenheit_low == pytest.approx(64.4)


def test_forecast_freezing_point() -> None:
    payload = {'main': {'temp': 0.0}}

    result = msgspec.convert(payload, type=Forecast)
    assert result.fahrenheit == pytest.approx(32.0)


def test_forecast_condition(forecast: Forecast) -> None:
    assert forecast.condition == 'Rain'


def test_forecast_description(forecast: Forecast) -> None:
    assert forecast.description == 'Light Rain'


def test_forecast_humidity(forecast: Forecast) -> None:
    assert forecast.humidity == 55


def test_forecast_pressure(forecast: Forecast) -> None:
    assert forecast.pressure == 1013


def test_forecast_wind(forecast: Forecast) -> None:
    assert forecast.wind_kmh == pytest.approx(36.0)
    assert forecast.wind_mph == pytest.approx(22.3694, abs=0.001)


def test_forecast_without_weather() -> None:
    result = msgspec.convert({'weather': []}, type=Forecast)

    assert result.condition is None
    assert result.description is None


def test_forecast_defaults() -> None:
    forecast = Forecast()

    assert forecast.celsius is None
    assert forecast.city is None
    assert forecast.country is None
    assert forecast.humidity is None
    assert forecast.pressure is None


def test_forecast_fahrenheit_without_temperature() -> None:
    result = msgspec.convert({}, type=Forecast)

    assert result.fahrenheit is None
    assert result.fahrenheit_high is None
    assert result.fahrenheit_low is None


def test_forecast_wind_without_speed() -> None:
    result = msgspec.convert({}, type=Forecast)

    assert result.wind_kmh is None
    assert result.wind_mph is None


def test_forecast_date_without_timestamp() -> None:
    result = msgspec.convert({}, type=Forecast)
    assert result.date == 'Unknown'
