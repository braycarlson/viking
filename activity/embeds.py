from __future__ import annotations

import discord

from typing_extensions import TYPE_CHECKING

from core.time import SECONDS_PER_HOUR, SECONDS_PER_MINUTE

if TYPE_CHECKING:
    from datetime import timedelta

    from activity.models import LastSeen, MemberWrapped


NO_DATA = 'There is no data yet.'


def duration_format(delta: timedelta) -> str:
    seconds = int(delta.total_seconds())
    hours, remainder = divmod(seconds, SECONDS_PER_HOUR)
    minutes, _ = divmod(remainder, SECONDS_PER_MINUTE)

    if hours > 0:
        return f'{hours}h {minutes}m'

    return f'{minutes}m'


def graph_embed(title: str, colour: discord.Colour) -> discord.Embed:
    embed = discord.Embed(title=title, colour=colour)
    embed.set_image(url='attachment://social.png')

    return embed


def last_seen_embed(
    member: discord.Member,
    last_seen: LastSeen,
    colour: discord.Colour
) -> discord.Embed:
    title = f'{member.display_name} Last Seen'

    embed = discord.Embed(title=title, colour=colour)
    embed.set_thumbnail(url=member.display_avatar.url)

    status = last_seen.status

    if status is None:
        embed.description = NO_DATA

        return embed

    if status.ended_at is None:
        moment = discord.utils.format_dt(status.started_at, 'R')
        online = f'Online now, since {moment}'
    else:
        moment = discord.utils.format_dt(status.ended_at, 'R')
        online = f'Last online {moment}'

    embed.add_field(inline=False, name='Status', value=online)

    game = last_seen.game

    if game is not None and game.name is not None:
        if game.ended_at is None:
            played = f'Playing **{game.name}** now'
        else:
            moment = discord.utils.format_dt(game.ended_at, 'R')
            played = f'**{game.name}** - {moment}'

        embed.add_field(inline=False, name='Last Game', value=played)

    voice = last_seen.voice

    if voice is not None and voice.channel_name is not None:
        if voice.ended_at is None:
            joined = f'In **{voice.channel_name}** now'
        else:
            moment = discord.utils.format_dt(voice.ended_at, 'R')
            joined = f'**{voice.channel_name}** - {moment}'

        embed.add_field(inline=False, name='Last Voice', value=joined)

    return embed


def leaderboard_embed(
    title: str,
    entries: list[tuple[str, str]],
    colour: discord.Colour
) -> discord.Embed:
    embed = discord.Embed(title=title, colour=colour)

    if not entries:
        embed.description = NO_DATA

        return embed

    lines = [
        f'`{index:>2}` **{label}** - {value}'
        for index, (label, value) in enumerate(entries, start=1)
    ]

    embed.description = '\n'.join(lines)

    return embed


def wrapped_embed(
    member: discord.Member,
    wrapped: MemberWrapped,
    colour: discord.Colour
) -> discord.Embed:
    title = f'{member.display_name} Wrapped'

    embed = discord.Embed(title=title, colour=colour)
    embed.set_thumbnail(url=member.display_avatar.url)

    has_data = bool(
        wrapped.games
        or wrapped.artists
        or wrapped.game_time
        or wrapped.voice_time
        or wrapped.online_time
    )

    if not has_data:
        embed.description = NO_DATA

        return embed

    if wrapped.games:
        games = '\n'.join(
            f'`{index:>2}` **{stat.name}** - {duration_format(stat.duration)}'
            for index, stat in enumerate(wrapped.games, start=1)
        )

        embed.add_field(inline=False, name='Top Games', value=games)

    if wrapped.artists:
        artists = '\n'.join(
            f'`{index:>2}` **{stat.artist}** - {duration_format(stat.duration)}'
            for index, stat in enumerate(wrapped.artists, start=1)
        )

        embed.add_field(inline=False, name='Top Artists', value=artists)

    embed.add_field(name='Time in Voice', value=duration_format(wrapped.voice_time))
    embed.add_field(name='Time Online', value=duration_format(wrapped.online_time))
    embed.add_field(name='Time in Game', value=duration_format(wrapped.game_time))

    if wrapped.channel is not None and wrapped.channel.channel_name is not None:
        embed.add_field(
            inline=False,
            name='Favourite Channel',
            value=wrapped.channel.channel_name
        )

    if wrapped.longest is not None and wrapped.longest.name is not None:
        longest = f'**{wrapped.longest.name}** - {duration_format(wrapped.longest.duration)}'
        embed.add_field(inline=False, name='Longest Session', value=longest)

    return embed
