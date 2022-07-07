import discord

from discord.ext import commands
from model.fortnite import Lifetime, Mode
from utilities.request import fetch


class Fortnite(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
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
    async def fortnite(self, ctx, platform: str, *, username: str):
        """
        *fortnite <platform> <username>

        A command that displays a player's Fortnite statistics,
        including solo, duo, squad and lifetime records.
        """

        async with ctx.typing():
            url = f"https://api.fortnitetracker.com/v1/profile/{platform}/{username}"
            data = await fetch(self.viking.session, url, headers=self.headers)

            # If a username is not found, the API responds with an error
            # message in a JSON object with a single key-value pair.

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


async def setup(viking):
    fortnite = Fortnite(viking)
    await viking.add_cog(fortnite)
