from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from discord import app_commands

from core.db.registry import databases
from roles.repository import RoleRepository

if TYPE_CHECKING:
    from discord import Interaction


async def role_autocomplete(
    interaction: Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    if interaction.guild_id is None:
        return []

    configuration = databases.guild(str(interaction.guild_id))

    if configuration is None:
        return []

    repository = RoleRepository(configuration.session)
    names = await repository.names_search(current)

    return [
        app_commands.Choice(name=name, value=name)
        for name in dict.fromkeys(names)
    ]
