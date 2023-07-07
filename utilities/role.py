from __future__ import annotations

from model.role import DiscordRoleError
from sqlalchemy import func
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cogs.roles import Roles
    from sqlalchemy.engine.result import RowProxy


async def check_for_role(self: Roles, name: str) -> RowProxy:
    """A function to check for the existence of a role."""

    name = name.lower()

    return (
        await self.viking.guild.role
        .query
        .where(func.lower(self.viking.guild.role.name) == name)
        .gino
        .scalar()
    )

async def get_role_by_id(self: Roles, identifier: int | str) -> str:
    """A function to get a role by ID from the database."""

    try:
        role_id = int(identifier)
    except ValueError:
        role = identifier.lower()
        return await get_role_by_name(self, role)
    else:
        row = (
            await self.viking.guild.role
            .select('id')
            .where(self.viking.guild.role.id == role_id)
            .gino
            .scalar()
        )

        if row is None:
            raise DiscordRoleError

        return row


async def get_role_by_name(self: Roles, role_name: str) -> RowProxy:
    """A function to get a role by name from the database."""

    row = (
        await self.viking.guild.role
        .query
        .where(func.lower(self.viking.guild.role.name) == role_name)
        .gino
        .scalar()
    )

    if row is None:
        raise DiscordRoleError

    return row
