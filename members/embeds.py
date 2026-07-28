from __future__ import annotations

import discord

from typing_extensions import TYPE_CHECKING

from core.text import list_format

if TYPE_CHECKING:
    from members.models import DiscordMember
    from roles.models import DiscordRole


def about_embed(
    member: DiscordMember,
    role: DiscordRole,
    colour: discord.Colour
) -> discord.Embed:
    embed = discord.Embed(colour=colour)

    embed.add_field(inline=False, name='Discord ID', value=str(member.identifier))
    embed.add_field(inline=False, name='Name', value=member.name)

    if member.nickname is not None:
        embed.add_field(inline=False, name='Nickname', value=member.nickname)

    embed.add_field(inline=False, name='Role', value=role.name)
    embed.add_field(inline=False, name='Created At', value=member.created)
    embed.add_field(inline=False, name='Joined At', value=member.joined)

    if member.updated_at is not None:
        embed.add_field(inline=False, name='Updated At', value=member.updated)

    if member.previous_name is not None:
        previous_name = list_format(member.previous_name, symbol='bullet', sort=False)
        embed.add_field(inline=False, name='Previous Names', value=previous_name)

    if member.previous_nickname is not None:
        previous_nickname = list_format(member.previous_nickname, symbol='bullet', sort=False)
        embed.add_field(inline=False, name='Previous Nicknames', value=previous_nickname)

    return embed
