from __future__ import annotations

import msgspec

from typing_extensions import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from core.http import RequestError, fetch
from weather import embeds
from weather.models import Forecast

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from bot import Viking


class Weather(commands.Cog):
    def __init__(self, viking: Viking) -> None:
        self.viking = viking

    @commands.hybrid_command(description='Display the forecast for a location.')
    @commands.cooldown(rate=60, per=60.0, type=commands.BucketType.default)
    @app_commands.describe(location='The location to get the forecast for.')
    async def forecast(self, ctx: Context, *, location: str) -> None:
        """
        *forecast <location>

        A command that displays the forecast for a location.
        """

        await ctx.typing()

        params = {
            'appid': self.viking.owm_api_key,
            'q': location,
            'units': 'metric',
        }

        url = f'{self.viking.owm_api_url}/weather'

        try:
            response = await fetch(self.viking.session, url, params=params)
        except RequestError:
            message = 'No location found.'
            await ctx.send(message)

            return

        forecast = msgspec.convert(response, type=Forecast)

        embed = embeds.forecast_embed(forecast, self.viking.colour)
        await ctx.send(embed=embed)


async def setup(viking: Viking) -> None:
    weather = Weather(viking)
    await viking.add_cog(weather)
