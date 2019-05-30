import discord
import re
from discord.ext import commands
from typing import Tuple
from utilities.checks import is_channel
from utilities.request import fetch


class Mode:
    def __init__(self, data, key):
        self._mode = data.get('stats').get(key)

    @property
    def kills(self) -> str:
        if self._mode is None:
            return '0'

        return self._mode.get('kills').get('displayValue')

    @property
    def matches(self) -> str:
        if self._mode is None:
            return '0'

        return self._mode.get('matches').get('displayValue')

    @property
    def wlr(self) -> str:
        if self._mode is None:
            return '0.00'

        return self._mode.get('winRatio').get('displayValue')

    @property
    def kdr(self) -> str:
        if self._mode is None:
            return '0.00'

        return self._mode.get('kd').get('displayValue')

    @property
    def wins(self) -> str:
        if self._mode is None:
            return '0'

        return self._mode.get('top1').get('displayValue')


# The TRN API includes a 'Lifetime' statistic, but due to formatting
# inconsistencies; I have opted to calculate it from the core modes.

class Lifetime:
    def __init__(self, solo, duo, squad):
        self._solo = solo
        self._duo = duo
        self._squad = squad

    @staticmethod
    def sumof(*args: Tuple[str]) -> int:
        """
        A function to convert a tuple of numeric strings to integers,
        and then add the sum of the integers.
        """

        pattern = re.compile('[^0-9]+')
        integers = [int(pattern.sub('', arg)) for arg in args]

        return sum(integers)

    @property
    def kills(self) -> str:
        total = self.sumof(
            self._solo.kills,
            self._duo.kills,
            self._squad.kills
        )

        return f"{total:,}"

    @property
    def matches(self) -> str:
        total = self.sumof(
            self._solo.matches,
            self._duo.matches,
            self._squad.matches
        )

        return f"{total:,}"

    @property
    def wlr(self) -> str:
        wins = self.sumof(
            self._solo.wins,
            self._duo.wins,
            self._squad.wins
        )

        matches = self.sumof(
            self._solo.matches,
            self._duo.matches,
            self._squad.matches
        )

        total = (wins / matches) * 100
        return f"{total:.2f}"

    @property
    def kdr(self) -> str:
        kills = self.sumof(
            self._solo.kills,
            self._duo.kills,
            self._squad.kills
        )

        wins = self.sumof(
            self._solo.wins,
            self._duo.wins,
            self._squad.wins
        )

        matches = self.sumof(
            self._solo.matches,
            self._duo.matches,
            self._squad.matches
        )

        total = kills / (matches - wins)
        return f"{total:.2f}"

    @property
    def wins(self) -> str:
        total = self.sumof(
            self._solo.wins,
            self._duo.wins,
            self._squad.wins
        )

        return f"{total:,}"


class Fortnite(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.session = viking.session
        self.trn_api_key = viking.trn_api_key
        self.headers = {"trn-api-key": self.trn_api_key}

    @staticmethod
    def statistics(mode):
        return f"""
                Kills: {mode.kills}
                Matches: {mode.matches}
                Win Ratio: {mode.wlr}%
                K/D Ratio: {mode.kdr}
                Wins: {mode.wins}
               """

    @commands.command(aliases=['fn'])
    @commands.cooldown(rate=1, per=3.0, type=commands.BucketType.default)
    @is_channel(579830092352716820)
    async def fortnite(self, ctx, platform: str, *, username: str):
        """
        *fortnite <platform> <username>

        A command that displays a player's Fortnite statistics,
        including solo, duo, squad and lifetime records.
        """

        async with ctx.typing():
            url = f"https://api.fortnitetracker.com/v1/profile/{platform}/{username}"
            data = await fetch(self.session, url, headers=self.headers)

            # If a username is not found, the API responds with an error
            # message in a dictionary with a single key-value pair.

            if len(data) > 1:
                solo = Mode(data, 'p2')
                duo = Mode(data, 'p10')
                squad = Mode(data, 'p9')
                lifetime = Lifetime(solo, duo, squad)

                solo = self.statistics(solo)
                duo = self.statistics(duo)
                squad = self.statistics(squad)
                lifetime = self.statistics(lifetime)

                embed = discord.Embed(title=username, colour=self.viking.color)
                embed.add_field(inline=False, name='Solo', value=solo)
                embed.add_field(inline=False, name='Duo', value=duo)
                embed.add_field(inline=False, name='Squad', value=squad)
                embed.add_field(inline=False, name='Lifetime', value=lifetime)

                await ctx.send(embed=embed)
            else:
                await ctx.send('Username not found.')


def setup(viking):
    viking.add_cog(Fortnite(viking))
