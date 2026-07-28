from __future__ import annotations

import contextlib

import discord

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from discord import Interaction


class AuthorView(discord.ui.View):
    def __init__(self, author_identifier: int, *, timeout: float | None) -> None:
        super().__init__(timeout=timeout)

        self.author_identifier = author_identifier
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.author_identifier:
            message = 'This is not your menu.'
            await interaction.response.send_message(message, ephemeral=True)

            return False

        return True

    async def on_timeout(self) -> None:
        if self.message is None:
            return

        with contextlib.suppress(discord.HTTPException):
            await self.message.edit(view=None)
