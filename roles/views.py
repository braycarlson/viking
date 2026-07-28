from __future__ import annotations

import discord

from typing_extensions import TYPE_CHECKING

from core.limits import BUTTON_LABEL_LENGTH_MAX, SELECT_VALUES_MAX
from core.views import AuthorView

if TYPE_CHECKING:
    import re

    from discord import Interaction


PANEL_TIMEOUT_SECONDS = 120.0


class RoleToggleButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r'role:(?P<id>\d+)'
):
    def __init__(self, role: discord.Role) -> None:
        self.role = role

        super().__init__(
            discord.ui.Button(
                label=role.name[:BUTTON_LABEL_LENGTH_MAX],
                style=discord.ButtonStyle.secondary,
                custom_id=f'role:{role.id}'
            )
        )

    @classmethod
    async def from_custom_id(
        cls,
        interaction: Interaction,
        item: discord.ui.Button,  # noqa: ARG003
        match: re.Match[str],
        /
    ) -> RoleToggleButton:
        role_identifier = int(match['id'])
        role = interaction.guild.get_role(role_identifier)

        if role is None:
            message = 'That role no longer exists.'
            raise ValueError(message)

        return cls(role)

    async def callback(self, interaction: Interaction) -> None:
        member = interaction.user
        role = self.role

        try:
            if role in member.roles:
                await member.remove_roles(role)
                message = f'Removed the {role.name} role.'
            else:
                await member.add_roles(role)
                message = f'Added the {role.name} role.'
        except discord.Forbidden:
            message = f'I do not have permission to manage the {role.name} role.'
        except discord.HTTPException:
            message = f'The {role.name} role could not be updated.'

        await interaction.response.send_message(message, ephemeral=True)


class RolePanelSelect(discord.ui.RoleSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder='Select the roles to include...',
            min_values=1,
            max_values=SELECT_VALUES_MAX
        )

    async def callback(self, interaction: Interaction) -> None:
        roles = [role for role in self.values if role.is_assignable()]

        if not roles:
            message = 'None of those roles can be assigned by me.'
            await interaction.response.edit_message(content=message, view=None)

            return

        view = discord.ui.View(timeout=None)

        for role in roles:
            view.add_item(RoleToggleButton(role))

        content = 'Click a button to toggle a role:'
        await interaction.channel.send(content, view=view)

        message = 'The role panel was posted.'
        await interaction.response.edit_message(content=message, view=None)


class RolePanelBuilderView(AuthorView):
    def __init__(self, author_identifier: int) -> None:
        super().__init__(author_identifier, timeout=PANEL_TIMEOUT_SECONDS)

        self.add_item(RolePanelSelect())
