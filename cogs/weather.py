import discord
import pyowm
from discord.ext import commands
from functools import partial


class Weather:
    def __init__(self, viking):
        self.viking = viking
        self.color = viking.color
        self.owm_api_key = viking.owm_api_key

    @commands.command()
    async def forecast(self, ctx, *, city):
        """*forecast <location>

        A command that will return the forecast of a specified location.
        """

        owm = pyowm.OWM(self.owm_api_key)

        observation = await self.viking.loop.run_in_executor(
            None, partial(owm.weather_at_place, city))

        location = observation.get_location()
        weather = observation.get_weather()
        time = observation.get_reception_time('date')

        name = location.get_name()
        country = location.get_country()
        longitude = location.get_lon()
        latitude = location.get_lat()

        temperature_celsius = weather.get_temperature('celsius')['temp']
        temperature_fahrenheit = weather.get_temperature('fahrenheit')['temp']
        low_celsius = weather.get_temperature('celsius')['temp_min']
        high_celsius = weather.get_temperature('celsius')['temp_max']
        low_fahrenheit = weather.get_temperature('fahrenheit')['temp_min']
        high_fahrenheit = weather.get_temperature('fahrenheit')['temp_max']
        wind = weather.get_wind()
        description = weather.get_detailed_status().title()
        humidity = weather.get_humidity()
        pressure = weather.get_pressure()['press']

        degree = '\N{DEGREE SIGN}'
        wind_kmh = round(wind['speed'] * 3600 / 1000, 2)
        wind_mph = round(wind['speed'] / 0.44704, 2)

        embed = discord.Embed(colour=self.color)
        embed.add_field(inline=False, name='City', value=name)
        embed.add_field(inline=False, name='Country', value=country)
        embed.add_field(inline=False, name='Coordinates', value=f"{latitude}, {longitude}")
        embed.add_field(inline=False, name='Temperature', value=f"{temperature_celsius}{degree}C / {temperature_fahrenheit}{degree}F")
        embed.add_field(inline=False, name='Low', value=f"{low_celsius}{degree}C / {low_fahrenheit}{degree}F")
        embed.add_field(inline=False, name='High', value=f"{high_celsius}{degree}C / {high_fahrenheit}{degree}F")
        embed.add_field(inline=False, name='Description', value=description)
        embed.add_field(inline=False, name='Humidity', value=f"{humidity}%")
        embed.add_field(inline=False, name='Wind', value=f"{wind_kmh} km/h / {wind_mph} mph")
        embed.add_field(inline=False, name='Pressure', value=f"{pressure} hpa")
        embed.add_field(inline=False, name='Observation', value=time.strftime('%I:%M %p'))

        await ctx.send(embed=embed)


def setup(viking):
    viking.add_cog(Weather(viking))
