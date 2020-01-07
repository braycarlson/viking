import datetime
import discord
from database.model import NHLTeams, NHLPlayers
from discord.ext import commands
from utilities.format import alphabet_and_spaces
from utilities.nhl import (
    Game,
    GoalieSingleSeason,
    PlayerSingleSeason,
    get_player_id,
    get_player_single_season,
    get_schedule,
    get_team_id,
    get_team_schedule
)
from utilities.pagination import Pages


class PlayerPages(Pages):
    def __init__(self, ctx, entries):
        super().__init__(ctx, entries=entries, per_page=1)

    def get_page(self, page):
        return self.entries[page - 1]

    def prepare_embed(self, player, page, *, first=False):
        if isinstance(player, NHLPlayers):
            self.embed = embed = discord.Embed(
                colour=discord.Colour.purple(),
                title='About'
            )

            embed.add_field(
                inline=False,
                name='Name',
                value=f"{player.full_name} (#{player.number})"
            )
            embed.add_field(
                inline=False,
                name='Birthday',
                value=datetime.datetime
                .strptime(player.birthdate, '%Y-%m-%d')
                .strftime('%B %d, %Y')
            )
            embed.add_field(
                inline=False,
                name='Age',
                value=player.age
            )

            if player.province:
                born = f"{player.city}, {player.province}, {player.country}"
            else:
                born = f"{player.city}, {player.country}"

            embed.add_field(
                inline=False,
                name='Born',
                value=born
            )
            embed.add_field(
                inline=False,
                name='Height',
                value=player.height
            )
            embed.add_field(
                inline=False,
                name='Weight',
                value=player.weight
            )
            embed.add_field(
                inline=False,
                name='Position',
                value=player.position_name
            )
            embed.add_field(
                inline=False,
                name='Team',
                value=player.team_name
            )

        if isinstance(player, PlayerSingleSeason):
            self.embed = embed = discord.Embed(
                colour=discord.Colour.purple(),
                title='Statistics'
            )

            embed.add_field(
                inline=False,
                name='Games',
                value=player.games
            )
            embed.add_field(
                inline=False,
                name='Shots',
                value=player.shots
            )
            embed.add_field(
                inline=False,
                name='Goals',
                value=player.goals
            )
            embed.add_field(
                inline=False,
                name='Assists',
                value=player.assists
            )
            embed.add_field(
                inline=False,
                name='Points',
                value=player.points
            )
            embed.add_field(
                inline=False,
                name='Powerplay Goals',
                value=player.powerplay_goals
            )
            embed.add_field(
                inline=False,
                name='Shot Percentage',
                value=f"{player.shot_percentage}%"
            )
            embed.add_field(
                inline=False,
                name='Hits',
                value=player.hits
            )

        if isinstance(player, GoalieSingleSeason):
            self.embed = embed = discord.Embed(
                colour=discord.Colour.purple(),
                title='Statistics'
            )

            embed.add_field(
                inline=False,
                name='Games',
                value=player.games
            )
            embed.add_field(
                inline=False,
                name='Wins',
                value=player.wins
            )
            embed.add_field(
                inline=False,
                name='Losses',
                value=player.losses
            )
            embed.add_field(
                inline=False,
                name='Shutouts',
                value=player.shutouts
            )
            embed.add_field(
                inline=False,
                name='Saves',
                value=player.saves
            )
            embed.add_field(
                inline=False,
                name='Shots Against',
                value=player.shots_against
            )
            embed.add_field(
                inline=False,
                name='Goals Against',
                value=player.goals_against
            )
            embed.add_field(
                inline=False,
                name='Save Percentage',
                value=f"{round(float(player.save_percentage) * 100, 2)}%"
            )

        if self.maximum_pages > 1:
            text = f'Page {page}/{self.maximum_pages}'
            embed.set_footer(text=text)


class SchedulePages(Pages):
    def __init__(self, ctx, entries):
        super().__init__(ctx, entries=entries, per_page=1)

    def get_page(self, page):
        return self.entries[page - 1]

    def prepare_embed(self, game, page, *, first=False):
        today = datetime.date.today()
        time = today.strftime('%B %d, %Y')

        self.embed = embed = discord.Embed(
            colour=discord.Colour.purple(),
            title=f"NHL Schedule for {time}"
        )

        embed.add_field(
            inline=False,
            name='Home Team',
            value=f"{game.home_name} ({game.home_team_record})"
        )

        embed.add_field(
            inline=False,
            name='Away Team',
            value=f"{game.away_name} ({game.away_team_record})"
        )

        embed.add_field(
            inline=False,
            name='Venue',
            value=game.venue_name
        )

        if self.maximum_pages > 1:
            text = f'Page {page}/{self.maximum_pages}'
            embed.set_footer(text=text)


class NHL(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.session = viking.session

    @commands.group()
    async def nhl(self, ctx):
        pass

    @nhl.command(name='game')
    async def game(self, ctx, *, team_name: str):
        """
        *nhl game <team>

        A command that displays information about an active,
        completed or upcoming game from today.
        """

        name = alphabet_and_spaces(team_name)
        team_id = await get_team_id(self.viking, ctx, name)

        if team_id is None:
            return await ctx.send('No team found.')

        today = datetime.date.today()
        time = today.strftime('%B %d, %Y')

        schedule = await get_team_schedule(self.session, today, team_id)
        dates = schedule.get('dates')

        if not dates:
            return await ctx.send('No game found.')

        embed = discord.Embed(
            inline=False,
            colour=self.viking.color,
            title=f"{time} \u200b"
        )

        for date in dates:
            for games in date.get('games'):
                game = Game(games)

                embed.add_field(
                    inline=False,
                    name='Home Team',
                    value=f"{game.home_name} ({game.home_team_record})"
                )
                embed.add_field(
                    inline=False,
                    name='Away Team',
                    value=f"{game.away_name} ({game.away_team_record})"
                )

                if game.status == 'Live' or game.status == 'Final':
                    embed.add_field(
                        inline=False,
                        name='Status',
                        value=f"{game.status}"
                    )
                    embed.add_field(
                        inline=False,
                        name='Score',
                        value=f"{game.home_score}-{game.away_score}"
                    )
                else:
                    embed.add_field(
                        inline=False,
                        name='Status',
                        value='Pending'
                    )

        await ctx.send(embed=embed)

    @nhl.command(name='player')
    async def player(self, ctx, *, player_name: str):
        """
        *nhl player <player>

        A command that displays trivial information about a player,
        and their statistics from the current season.
        """

        name = alphabet_and_spaces(player_name)
        player_id = await get_player_id(self.viking, ctx, name)

        if player_id is None:
            return await ctx.send('No player found.')

        data = []

        player = await NHLPlayers.query.where(
            NHLPlayers.player_id == player_id
        ).gino.first()

        data.append(player)

        season = await get_player_single_season(
            self.session,
            player_id
        )

        for splits in season.get('stats'):
            for statistics in splits.get('splits'):
                statistic = statistics.get('stat')

                if (player.position_type == 'Forward' or
                        player.position_type == 'Defenseman'):
                    season = PlayerSingleSeason(statistic)

                if player.position_type == 'Goalie':
                    season = GoalieSingleSeason(statistic)

                data.append(season)

        try:
            pages = PlayerPages(ctx, data)
            await pages.paginate()
        except Exception:
            pass
        finally:
            await ctx.message.delete()

    @nhl.command(name='schedule')
    async def schedule(self, ctx):
        """
        *nhl schedule

        A command that displays information about every game occuring today.
        """

        data = []

        today = datetime.date.today()
        schedule = await get_schedule(self.session, today)
        dates = schedule.get('dates')

        if not dates:
            time = today.strftime('%B %d, %Y')
            return await ctx.send(f"No game found for {time}.")

        for date in dates:
            for games in date.get('games'):
                game = Game(games)
                data.append(game)

        try:
            pages = SchedulePages(ctx, data)
            await pages.paginate()
        except Exception:
            pass
        finally:
            await ctx.message.delete()

    @nhl.command(name='team')
    async def team(self, ctx, *, team_name: str):
        """
        *nhl team <team>

        A command that displays trivial information about a team.
        """

        name = alphabet_and_spaces(team_name)
        team_id = await get_team_id(self.viking, ctx, name)

        if team_id is None:
            return await ctx.send('No team found.')

        embed = discord.Embed(
            inline=False,
            colour=self.viking.color,
            title='Team'
        )

        team = await NHLTeams.query.where(
            NHLTeams.team_id == team_id
        ).gino.first()

        embed.add_field(
            inline=False,
            name='Name',
            value=team.name
        )
        embed.add_field(
            inline=False,
            name='Abbreviation',
            value=team.abbreviation
        )
        embed.add_field(
            inline=False,
            name='Venue',
            value=team.venue_name
        )
        embed.add_field(
            inline=False,
            name='Division',
            value=team.division_name
        )
        embed.add_field(
            inline=False,
            name='Conference',
            value=team.conference_name
        )
        embed.add_field(
            inline=False,
            name='First Year of Play',
            value=team.first_year_of_play
        )
        embed.add_field(
            inline=False,
            name='Website',
            value=team.official_website
        )

        await ctx.send(embed=embed)


def setup(viking):
    viking.add_cog(NHL(viking))
