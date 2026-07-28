from __future__ import annotations

import contextlib

import discord

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from roles.models import DiscordRole


class RoleCard(discord.ui.LayoutView):
    def __init__(self, role: DiscordRole, colour: discord.Colour) -> None:
        super().__init__()

        accent = colour

        if role.colour:
            with contextlib.suppress(ValueError):
                accent = discord.Colour.from_str(role.colour)

        container = discord.ui.Container(accent_colour=accent)
        container.add_item(discord.ui.TextDisplay(f'## {role.name}'))
        container.add_item(discord.ui.Separator())

        if role.mentionable:
            mentionable = 'Yes'
        else:
            mentionable = 'No'

        if role.hoist:
            hoisted = 'Yes'
        else:
            hoisted = 'No'

        details = '\n'.join([
            f'**Position:** {role.position}',
            f'**Colour:** {role.colour}',
            f'**Mentionable:** {mentionable}',
            f'**Hoisted:** {hoisted}',
            f'**Created:** {role.created}',
        ])

        container.add_item(discord.ui.TextDisplay(details))

        self.add_item(container)
