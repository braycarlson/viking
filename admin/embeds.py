from __future__ import annotations

import discord

from core.text import list_format


def hidden_embed(names: list[str], colour: discord.Colour) -> discord.Embed:
    command = list_format(names, symbol='asterisk', sort=True)

    embed = discord.Embed(colour=colour)
    embed.add_field(name='Hidden Commands', value=command)

    return embed
