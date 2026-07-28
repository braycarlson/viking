from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from members.repository import MemberRepository

if TYPE_CHECKING:
    from discord import Member

    from bot import Viking


class MemberEvent:
    def __init__(self, viking: Viking) -> None:
        self.viking = viking

    @property
    def repository(self) -> MemberRepository:
        return MemberRepository(self.viking.guild.session)

    async def member_ban(self, identifier: int) -> None:
        await self.repository.ban(identifier)

    async def member_create(self, member: Member) -> None:
        await self.repository.create(member)

    async def member_is_banned(self, identifier: int) -> bool:
        return await self.repository.is_banned(identifier)

    async def member_is_removed(self, identifier: int) -> bool:
        return await self.repository.is_removed(identifier)

    async def member_remove(self, identifier: int) -> None:
        await self.repository.remove(identifier)

    async def member_restore(self, identifier: int) -> None:
        await self.repository.restore(identifier)

    async def member_unban(self, identifier: int) -> None:
        await self.repository.unban(identifier)

    async def member_update(self, member: Member) -> None:
        previous_member = await self.repository.previous_record_get(member.id)

        if previous_member is None:
            return

        await self.previous_name_update(member, previous_member.name)
        await self.previous_nickname_update(member, previous_member.nickname)

        await self.repository.profile_update(
            member,
            removed_at=previous_member.removed_at,
            banned_at=previous_member.banned_at,
        )

    async def name_append(self, before: Member, after: Member) -> None:
        await self.repository.name_append(before, after)

    async def nickname_append(self, before: Member, after: Member) -> None:
        await self.repository.nickname_append(before, after)

    async def nickname_update(self, after: Member) -> None:
        await self.repository.nickname_update(after)

    async def previous_name_update(self, member: Member, name: str | None) -> None:
        if name is None:
            return

        if name != member.name:
            await self.repository.previous_name_prepend(member.id, name)

    async def previous_nickname_update(self, member: Member, nickname: str | None) -> None:
        if nickname is None:
            return

        if nickname != member.nick:
            await self.repository.previous_nickname_prepend(member.id, nickname)

    async def role_update(self, after: Member) -> None:
        await self.repository.role_update(after)
