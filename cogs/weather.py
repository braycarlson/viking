import discord

from discord.ext import commands
from model.weather import Forecast
from utilities.request import RequestError, fetch


BASE = 'http://api.openweathermap.org/data/2.5'


class Weather(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.owm_api_key = viking.owm_api_key

    @commands.command()
    @commands.cooldown(rate=60, per=60.0, type=commands.BucketType.default)
    async def forecast(self, ctx, *, location: str):
        """
        *forecast <location>

        A command that displays the forecast for a location.
        """

        params = {
            'appid': self.owm_api_key
        }

        url = f"{BASE}/weather?q={location}&units=metric"

        try:
            response = await fetch(self.viking.session, url, params=params)
        except RequestError:
            await ctx.send('No location found.')
        else:
            forecast = Forecast(response)

            degree = '\u00B0'

            embed = discord.Embed(colour=self.viking.color)
            embed.add_field(
                inline=False,
                name='Location',
                value=f"{forecast.city}, {forecast.country}"
            )
            embed.add_field(
                inline=False,
                name='Temperature',
                value=f"{round(forecast.temperature)}{degree}C "
                      f"/ {round(forecast.fahrenheit)}{degree}F"
            )
            embed.add_field(
                inline=False,
                name='Low',
                value=f"{round(forecast.low_temperature)}{degree}C "
                      f"/ {round(forecast.low_fahrenheit)}{degree}F"
            )
            embed.add_field(
                inline=False,
                name='High',
                value=f"{round(forecast.high_temperature)}{degree}C "
                      f"/ {round(forecast.high_fahrenheit)}{degree}F"
            )
            embed.add_field(
                inline=False,
                name='Weather',
                value=f"{forecast.condition}"
            )
            embed.add_field(
                inline=False,
                name='Description',
                value=f"{forecast.description}"
            )
            embed.add_field(
                inline=False,
                name='Humidity',
                value=f"{forecast.humidity}%"
            )
            embed.add_field(
                inline=False,
                name='Wind',
                value=f"{round(forecast.kmh_wind)} km/h / "
                      f"{round(forecast.mph_wind)} mph"
            )
            embed.add_field(
                inline=False,
                name='Pressure',
                value=f"{forecast.pressure} hpa"
            )
            embed.add_field(
                inline=False,
                name='Observation',
                value=forecast.date
            )

            await ctx.send(embed=embed)


async def setup(viking):
    weather = Weather(viking)
    await viking.add_cog(weather)
