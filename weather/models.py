from __future__ import annotations

import msgspec

from core.time import SECONDS_PER_HOUR, utc_format


FAHRENHEIT_OFFSET = 32
FAHRENHEIT_RATIO = 9 / 5

METRES_PER_KILOMETRE = 1000
METRES_SECOND_PER_MPH = 0.44704


def _fahrenheit(celsius: float | None) -> float | None:
    if celsius is None:
        return None

    return (celsius * FAHRENHEIT_RATIO) + FAHRENHEIT_OFFSET


class Condition(msgspec.Struct):
    description: str | None = None
    main: str | None = None


class Main(msgspec.Struct):
    humidity: int | None = None
    pressure: int | None = None
    temperature: float | None = msgspec.field(default=None, name='temp')
    temperature_max: float | None = msgspec.field(default=None, name='temp_max')
    temperature_min: float | None = msgspec.field(default=None, name='temp_min')


class System(msgspec.Struct):
    country: str | None = None


class Wind(msgspec.Struct):
    speed: float | None = None


class Forecast(msgspec.Struct):
    main: Main = msgspec.field(default_factory=Main)
    name: str | None = None
    system: System = msgspec.field(default_factory=System, name='sys')
    timestamp: int | None = msgspec.field(default=None, name='dt')
    weather: list[Condition] = []
    wind: Wind = msgspec.field(default_factory=Wind)

    @property
    def celsius(self) -> float | None:
        return self.main.temperature

    @property
    def celsius_high(self) -> float | None:
        return self.main.temperature_max

    @property
    def celsius_low(self) -> float | None:
        return self.main.temperature_min

    @property
    def city(self) -> str | None:
        return self.name

    @property
    def condition(self) -> str | None:
        if not self.weather:
            return None

        main = self.weather[0].main

        if main is None:
            return None

        return main.title()

    @property
    def country(self) -> str | None:
        return self.system.country

    @property
    def date(self) -> str:
        if self.timestamp is None:
            return 'Unknown'

        return utc_format(self.timestamp)

    @property
    def description(self) -> str | None:
        if not self.weather:
            return None

        description = self.weather[0].description

        if description is None:
            return None

        return description.title()

    @property
    def fahrenheit(self) -> float | None:
        return _fahrenheit(self.celsius)

    @property
    def fahrenheit_high(self) -> float | None:
        return _fahrenheit(self.celsius_high)

    @property
    def fahrenheit_low(self) -> float | None:
        return _fahrenheit(self.celsius_low)

    @property
    def humidity(self) -> int | None:
        return self.main.humidity

    @property
    def pressure(self) -> int | None:
        return self.main.pressure

    @property
    def wind_kmh(self) -> float | None:
        if self.wind.speed is None:
            return None

        return self.wind.speed * SECONDS_PER_HOUR / METRES_PER_KILOMETRE

    @property
    def wind_mph(self) -> float | None:
        if self.wind.speed is None:
            return None

        return self.wind.speed / METRES_SECOND_PER_MPH
