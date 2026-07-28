from __future__ import annotations

from dataclasses import dataclass
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    import discord

    from roles.models import DiscordRole
    from roles.repository import RoleRepository


@dataclass(kw_only=True)
class RoleSyncPlan:
    create: list[discord.Role]
    update: list[discord.Role]
    delete: list[int]


class RoleSynchronizer:
    def __init__(self, repository: RoleRepository) -> None:
        self.repository = repository

    @staticmethod
    def _changed(stored: DiscordRole, role: discord.Role) -> bool:
        return (
            stored.name != role.name or
            stored.colour != str(role.colour) or
            stored.hoist != role.hoist or
            stored.position != role.position or
            stored.managed != role.managed or
            stored.mentionable != role.mentionable or
            stored.is_default != role.is_default()
        )

    async def plan(self, guild: discord.Guild) -> RoleSyncPlan:
        stored = await self.repository.records_all()
        live = {role.id: role for role in guild.roles}

        create = [
            role
            for identifier, role in live.items()
            if identifier not in stored
        ]

        update = [
            role
            for identifier, role in live.items()
            if identifier in stored and self._changed(stored[identifier], role)
        ]

        delete = [
            identifier
            for identifier in stored
            if identifier not in live
        ]

        return RoleSyncPlan(create=create, update=update, delete=delete)

    async def prune(self, plan: RoleSyncPlan) -> None:
        if plan.delete:
            await self.repository.delete_many(plan.delete)

    async def upsert(self, plan: RoleSyncPlan) -> None:
        if plan.create:
            await self.repository.create_many(plan.create)

        if plan.update:
            await self.repository.update_many(plan.update)
