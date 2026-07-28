from __future__ import annotations

from dataclasses import dataclass
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    import discord

    from members.models import DiscordMember
    from members.repository import MemberRepository


@dataclass(kw_only=True)
class MemberSyncPlan:
    create: list[discord.Member]
    update: list[tuple[discord.Member, str | None, str | None]]
    restore: list[tuple[discord.Member, str | None, str | None]]
    remove: list[int]
    ban: list[int]
    unban: list[int]


class MemberSynchronizer:
    def __init__(self, repository: MemberRepository) -> None:
        self.repository = repository

    @staticmethod
    def _bans_plan(
        stored: dict[int, DiscordMember],
        banned_identifiers: set[int] | None
    ) -> tuple[list[int], list[int]]:
        if banned_identifiers is None:
            return [], []

        ban = [
            identifier
            for identifier in banned_identifiers
            if identifier in stored and stored[identifier].banned_at is None
        ]

        unban = [
            identifier
            for identifier, stored_member in stored.items()
            if stored_member.banned_at is not None and identifier not in banned_identifiers
        ]

        return ban, unban

    async def apply(self, plan: MemberSyncPlan) -> None:
        if plan.create:
            await self.repository.create_many(plan.create)

        if plan.restore:
            await self.repository.restore_many(plan.restore)

        if plan.update:
            await self.repository.profile_synchronize(plan.update)

        if plan.remove:
            await self.repository.remove_many(plan.remove)

        if plan.ban:
            await self.repository.ban_many(plan.ban)

        if plan.unban:
            await self.repository.unban_many(plan.unban)

    async def plan(
        self,
        guild: discord.Guild,
        banned_identifiers: set[int] | None
    ) -> MemberSyncPlan:
        stored = await self.repository.records_all()
        live = {member.id: member for member in guild.members}

        create = []
        update = []
        restore = []

        for identifier, member in live.items():
            stored_member = stored.get(identifier)

            if stored_member is None:
                create.append(member)
                continue

            name_changed = stored_member.name != member.name
            nickname_changed = stored_member.nickname != member.nick
            display_changed = stored_member.display_name != member.display_name
            role_changed = stored_member.role_identifier != member.top_role.id

            if name_changed:
                previous_name = stored_member.name
            else:
                previous_name = None

            if nickname_changed and stored_member.nickname is not None:
                previous_nickname = stored_member.nickname
            else:
                previous_nickname = None

            record = (member, previous_name, previous_nickname)

            if stored_member.removed_at is not None or stored_member.banned_at is not None:
                restore.append(record)
                continue

            if name_changed or nickname_changed or display_changed or role_changed:
                update.append(record)

        remove = [
            identifier
            for identifier, stored_member in stored.items()
            if identifier not in live and stored_member.removed_at is None
        ]

        ban, unban = self._bans_plan(stored, banned_identifiers)

        return MemberSyncPlan(
            create=create,
            update=update,
            restore=restore,
            remove=remove,
            ban=ban,
            unban=unban,
        )
