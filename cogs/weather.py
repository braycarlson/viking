import discord
from discord.ext import commands
from utilities.format import format_utc
from utilities.request import RequestError, fetch


BASE = 'http://api.openweathermap.org/data/2.5'


class Forecast:
    __slots__ = (
        'city',
        'country',
        'conditions',
        'condition',
        'description',
        'temperature',
        'low_temperature',
        'high_temperature',
        'wind',
        'humidity',
        'pressure',
        'observed'
    )

    def __init__(self, data):
        self.city = data.get('name')
        self.country = data.get('sys').get('country')
        self.conditions = data.get('weather')
        self.temperature = data.get('main').get('temp')
        self.low_temperature = data.get('main').get('temp_min')
        self.high_temperature = data.get('main').get('temp_max')
        self.wind = data.get('wind').get('speed')
        self.humidity = data.get('main').get('humidity')
        self.pressure = data.get('main').get('pressure')
        self.observed = data.get('dt')

        for condition in self.conditions:
            self.condition = condition.get('main').title()
            self.description = condition.get('description').title()

    @property
    def fahrenheit(self):
        return (self.temperature * 9/5) + 32

    @property
    def low_fahrenheit(self):
        return (self.low_temperature * 9/5) + 32

    @property
    def high_fahrenheit(self):
        return (self.high_temperature * 9/5) + 32

    @property
    def kmh_wind(self):
        return self.wind * 3600 / 1000

    @property
    def mph_wind(self):
        return self.wind / 0.44704

    @property
    def date(self):
        return format_utc(self.observed)


class Weather(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.owm_api_key = viking.owm_api_key
        self.session = viking.session

    @commands.command()
    @commands.cooldown(rate=60, per=60.0, type=commands.BucketType.default)
    async def forecast(self, ctx, *, location):
        """
        *forecast <location>

        A command that displays the forecast for a location.
        """

        params = {
            'appid': self.owm_api_key
        }

        url = f"{BASE}/weather?q={location}&units=metric"

        try:
            response = await fetch(self.session, url, params=params)
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


def setup(viking):
    viking.add_cog(Weather(viking))
