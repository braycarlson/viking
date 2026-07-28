from __future__ import annotations

import discord


def quote_embed(quote: str, author: str, colour: discord.Colour) -> discord.Embed:
    embed = discord.Embed(colour=colour)
    embed.add_field(name=quote, value=f'- {author}')

    return embed
