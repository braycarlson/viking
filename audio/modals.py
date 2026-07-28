from __future__ import annotations

import discord

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from discord import Interaction


NAME_LENGTH_MAX = 32


class SoundUploadModal(discord.ui.Modal, title='Add a Sound'):
    def __init__(
        self,
        store: Callable[[discord.Attachment, str | None, int], Awaitable[str]]
    ) -> None:
        super().__init__()

        self.store = store

        self.name = discord.ui.TextInput(
            max_length=NAME_LENGTH_MAX,
            placeholder='Leave this blank to use the filename.',
            required=False
        )

        self.upload = discord.ui.FileUpload(
            max_values=1,
            min_values=1,
            required=True
        )

        name_label = discord.ui.Label(
            text='Name',
            description='The name members will use to play the sound.',
            component=self.name
        )

        upload_label = discord.ui.Label(
            text='Sound',
            description='An audio file to add to the soundbank.',
            component=self.upload
        )

        self.add_item(name_label)
        self.add_item(upload_label)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        if not self.upload.values:
            message = 'No file was uploaded.'
            await interaction.followup.send(message, ephemeral=True)

            return

        attachment = self.upload.values[0]

        name = self.name.value.strip() or None

        message = await self.store(attachment, name, interaction.user.id)
        await interaction.followup.send(message, ephemeral=True)
