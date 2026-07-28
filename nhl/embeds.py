from __future__ import annotations

import discord
import msgspec

from typing_extensions import TYPE_CHECKING

from nhl.enums import GameStatus, Position
from nhl.models import FeaturedStatistics

if TYPE_CHECKING:
    from slapshot import PlayerLanding, Roster, StandingsResponse

    from nhl.models import Leader, ScheduledGame


NO_LEADERS = 'No leaders are available.'
NO_ROSTER = 'No players are on the roster.'
NO_STANDINGS = 'No standings are available.'


def _status(game: ScheduledGame) -> str:
    if game.is_final:
        return GameStatus.FINAL

    if game.is_live:
        return GameStatus.LIVE

    scheduled = game.scheduled

    if scheduled is None:
        return GameStatus.SCHEDULED

    return discord.utils.format_dt(scheduled, 'f')


def _statistics(player: PlayerLanding) -> str | None:
    featured = msgspec.convert(player.featured_stats or {}, type=FeaturedStatistics)
    statistics = featured.regular_season.sub_season

    if statistics.games_played == 0:
        return None

    if player.position == Position.GOALIE:
        return (
            f'{statistics.games_played} GP, '
            f'{statistics.wins} W, '
            f'{statistics.losses} L, '
            f'{statistics.save_percentage:.3f} SV%, '
            f'{statistics.goals_against_average:.2f} GAA'
        )

    return (
        f'{statistics.games_played} GP, '
        f'{statistics.goals} G, '
        f'{statistics.assists} A, '
        f'{statistics.points} P'
    )


def games_embed(
    title: str,
    games: list[ScheduledGame],
    empty: str,
    colour: discord.Colour
) -> discord.Embed:
    embed = discord.Embed(colour=colour, title=title)

    if not games:
        embed.description = empty

        return embed

    for game in games:
        embed.add_field(
            inline=False,
            name=game.matchup,
            value=_status(game)
        )

    return embed


def leaders_embed(leaders: list[Leader], colour: discord.Colour) -> discord.Embed:
    embed = discord.Embed(colour=colour, title='NHL Points Leaders')

    if not leaders:
        embed.description = NO_LEADERS

        return embed

    rows = [
        f'{rank}. {leader.entry}'
        for rank, leader in enumerate(leaders, 1)
    ]

    embed.add_field(
        inline=False,
        name='Points',
        value='\n'.join(rows)
    )

    return embed


def player_embed(player: PlayerLanding, colour: discord.Colour) -> discord.Embed:
    name = f'{player.first_name.default} {player.last_name.default}'

    embed = discord.Embed(
        colour=colour,
        title=f'{name} (#{player.sweater_number})'
    )

    if player.headshot is not None:
        embed.set_thumbnail(url=player.headshot)

    feet, inches = divmod(player.height_in_inches or 0, 12)

    birthplace = []

    if player.birth_city is not None:
        city = player.birth_city.default
        birthplace.append(city)

    if player.birth_state_province is not None:
        state = player.birth_state_province.default
        birthplace.append(state)

    if player.birth_country is not None:
        country = player.birth_country
        birthplace.append(country)

    embed.add_field(inline=False, name='Team', value=player.current_team_abbrev or 'None')
    embed.add_field(inline=False, name='Position', value=player.position or 'None')

    embed.add_field(
        inline=False,
        name='Height',
        value=f'{feet}\' {inches}"'
    )

    embed.add_field(
        inline=False,
        name='Weight',
        value=f'{player.weight_in_pounds} lbs'
    )

    embed.add_field(inline=False, name='Shoots', value=player.shoots_catches or 'None')
    embed.add_field(inline=False, name='Birthplace', value=', '.join(birthplace) or 'None')
    embed.add_field(inline=False, name='Born', value=player.birth_date or 'None')

    statistics = _statistics(player)

    if statistics is not None:
        embed.add_field(inline=False, name='Season', value=statistics)

    return embed


def roster_embed(team_name: str, roster: Roster, colour: discord.Colour) -> discord.Embed:
    embed = discord.Embed(
        colour=colour,
        title=f'{team_name} Roster'
    )

    positions = [
        ('Forwards', roster.forwards),
        ('Defensemen', roster.defensemen),
        ('Goalies', roster.goalies),
    ]

    for name, players in positions:
        if not players:
            continue

        ordered = sorted(players, key=lambda player: player.sweater_number or 0)

        rows = [
            f'#{player.sweater_number} '
            f'{player.first_name.default} {player.last_name.default}'
            for player in ordered
        ]

        embed.add_field(
            inline=False,
            name=name,
            value='\n'.join(rows)
        )

    if not embed.fields:
        embed.description = NO_ROSTER

    return embed


def standings_embed(response: StandingsResponse, colour: discord.Colour) -> discord.Embed:
    divisions: dict[str, list] = {}

    for team in response.standings:
        division = team.division_name or 'League'
        divisions.setdefault(division, []).append(team)

    embed = discord.Embed(
        colour=colour,
        title='NHL Standings'
    )

    if not divisions:
        embed.description = NO_STANDINGS

        return embed

    for division, teams in divisions.items():
        teams.sort(key=lambda team: team.division_sequence or 0)

        rows = [
            f'{team.division_sequence}. {team.team_abbrev.default} '
            f'{team.wins}-{team.losses}-{team.ot_losses} '
            f'- {team.points} pts'
            for team in teams
        ]

        embed.add_field(
            inline=False,
            name=division,
            value='\n'.join(rows)
        )

    return embed
