from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from members.repository import MemberRepository
from roles.repository import RoleRepository

if TYPE_CHECKING:
    from discord import Guild, Role

    from bot import Viking


class RoleEvent:
    def __init__(self, viking: Viking) -> None:
        self.viking = viking

    @property
    def member_repository(self) -> MemberRepository:
        return MemberRepository(self.viking.guild.session)

    @property
    def role_repository(self) -> RoleRepository:
        return RoleRepository(self.viking.guild.session)

    async def role_create(self, role: Role) -> None:
        await self.role_repository.create(role)

    async def role_delete(self, role_identifier: int) -> None:
        await self.role_repository.delete(role_identifier)

    async def role_replace(self, guild: Guild) -> None:
        stored = await self.member_repository.role_identifiers_get()

        assignments = [
            (member.id, member.top_role.id)
            for member in guild.members
            if member.id in stored and stored[member.id] != member.top_role.id
        ]

        if assignments:
            await self.member_repository.role_synchronize(assignments)

    async def role_update(self, role: Role) -> None:
        await self.role_repository.update(role)
