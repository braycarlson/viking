from __future__ import annotations

import discord

from core.text import list_format


def suggestion_embed(names: list[str], colour: discord.Colour) -> discord.Embed:
    suggestion = list_format(names, symbol='asterisk', sort=False)

    embed = discord.Embed(colour=colour)

    embed.add_field(
        name='Command not found. Did you mean...',
        value=suggestion
    )

    return embed
