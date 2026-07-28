from __future__ import annotations

import msgspec

from typing_extensions import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands
from slapshot import AsyncNHL, NHLError

from nhl import embeds
from nhl.api import TEAM_NAMES, player_get, team_get
from nhl.autocomplete import team_autocomplete
from nhl.models import GameSchedule, Leaders

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from bot import Viking


API_UNAVAILABLE = 'The NHL API is unavailable. Please try again later.'
LEADERS_MAX = 10

TEAM_FULL = {team: name for name, team in TEAM_NAMES.items()}


class NationalHockeyLeague(commands.Cog):
    def __init__(self, viking: Viking) -> None:
        self.viking = viking
        self.client = AsyncNHL()

    async def cog_unload(self) -> None:
        await self.client.close()

    # Commands

    @commands.hybrid_command(description='Display the NHL points leaders.')
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.default)
    async def leaders(self, ctx: Context) -> None:
        """
        *leaders

        A command that displays the NHL skater points leaders.
        """

        await ctx.typing()

        try:
            response = await self.client.players.skater_leaders(limit=LEADERS_MAX)
        except NHLError:
            message = API_UNAVAILABLE
            await ctx.send(message)

            return

        leaders = msgspec.convert(response, type=Leaders)

        embed = embeds.leaders_embed(leaders.points, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Display a player's profile.")
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.default)
    @app_commands.describe(player_name='The name of the player.')
    async def player(self, ctx: Context, *, player_name: str) -> None:
        """
        *player <name>

        A command that displays an NHL player's profile and current
        season statistics.
        """

        await ctx.typing()

        try:
            player = await player_get(self.client, player_name)
        except NHLError:
            message = API_UNAVAILABLE
            await ctx.send(message)

            return

        if player is None:
            message = f'Player "{player_name}" not found.'
            await ctx.send(message)

            return

        embed = embeds.player_embed(player, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Display a team's roster.")
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.default)
    @app_commands.describe(team_name='The name or abbreviation of the team.')
    @app_commands.autocomplete(team_name=team_autocomplete)
    async def roster(self, ctx: Context, *, team_name: str) -> None:
        """
        *roster <team>

        A command that displays a team's active roster.
        """

        await ctx.typing()

        team = team_get(team_name)

        try:
            roster = await self.client.teams.roster(team)
        except NHLError:
            message = API_UNAVAILABLE
            await ctx.send(message)

            return

        team_full = TEAM_FULL.get(team, team.value)

        embed = embeds.roster_embed(team_full, roster, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Display a team's weekly schedule.")
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.default)
    @app_commands.describe(team_name='The name or abbreviation of the team.')
    @app_commands.autocomplete(team_name=team_autocomplete)
    async def schedule(self, ctx: Context, *, team_name: str) -> None:
        """
        *schedule <team>

        A command that displays a team's schedule for the current week.
        """

        await ctx.typing()

        team = team_get(team_name)

        try:
            response = await self.client.schedule.club_week(team)
        except NHLError:
            message = API_UNAVAILABLE
            await ctx.send(message)

            return

        schedule = msgspec.convert(response, type=GameSchedule)
        team_full = TEAM_FULL.get(team, team.value)

        embed = embeds.games_embed(
            f'{team_full} Schedule',
            schedule.games,
            'No games are scheduled this week.',
            self.viking.colour
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Display today's NHL scores.")
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.default)
    async def scores(self, ctx: Context) -> None:
        """
        *scores

        A command that displays the scores for today's NHL games.
        """

        await ctx.typing()

        try:
            response = await self.client.games.scores()
        except NHLError:
            message = API_UNAVAILABLE
            await ctx.send(message)

            return

        schedule = msgspec.convert(response, type=GameSchedule)

        embed = embeds.games_embed(
            'NHL Scoreboard',
            schedule.games,
            'No games are scheduled today.',
            self.viking.colour
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display the current NHL standings.')
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.default)
    async def standings(self, ctx: Context) -> None:
        """
        *standings

        A command that displays the current NHL standings by division.
        """

        await ctx.typing()

        try:
            response = await self.client.standings.now()
        except NHLError:
            message = API_UNAVAILABLE
            await ctx.send(message)

            return

        embed = embeds.standings_embed(response, self.viking.colour)
        await ctx.send(embed=embed)


async def setup(viking: Viking) -> None:
    nhl = NationalHockeyLeague(viking)
    await viking.add_cog(nhl)
