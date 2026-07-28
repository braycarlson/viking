from __future__ import annotations

import discord

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from weather.models import Forecast


DEGREE_SYMBOL = '°'
UNKNOWN = 'Unknown'


def _rounded(value: float | None) -> str:
    if value is None:
        return UNKNOWN

    return str(round(value))


def _temperature(celsius: float | None, fahrenheit: float | None) -> str:
    if celsius is None and fahrenheit is None:
        return UNKNOWN

    metric = _rounded(celsius)
    imperial = _rounded(fahrenheit)

    return f'{metric}{DEGREE_SYMBOL}C / {imperial}{DEGREE_SYMBOL}F'


def forecast_embed(forecast: Forecast, colour: discord.Colour) -> discord.Embed:
    temperature = _temperature(forecast.celsius, forecast.fahrenheit)
    low = _temperature(forecast.celsius_low, forecast.fahrenheit_low)
    high = _temperature(forecast.celsius_high, forecast.fahrenheit_high)

    wind_kmh = _rounded(forecast.wind_kmh)
    wind_mph = _rounded(forecast.wind_mph)

    embed = discord.Embed(colour=colour)

    embed.add_field(
        inline=False,
        name='Location',
        value=f'{forecast.city}, {forecast.country}'
    )

    embed.add_field(inline=False, name='Temperature', value=temperature)
    embed.add_field(inline=False, name='Low', value=low)
    embed.add_field(inline=False, name='High', value=high)
    embed.add_field(inline=False, name='Weather', value=forecast.condition or UNKNOWN)
    embed.add_field(inline=False, name='Description', value=forecast.description or UNKNOWN)
    embed.add_field(inline=False, name='Humidity', value=f'{forecast.humidity}%')

    embed.add_field(
        inline=False,
        name='Wind',
        value=f'{wind_kmh} km/h / {wind_mph} mph'
    )

    embed.add_field(inline=False, name='Pressure', value=f'{forecast.pressure} hpa')
    embed.add_field(inline=False, name='Observation', value=forecast.date)

    return embed
