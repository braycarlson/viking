from __future__ import annotations

from datetime import datetime, UTC
from typing_extensions import TYPE_CHECKING

from sqlalchemy import cast, func, select, TEXT, update

from core.db.repository import RECORDS_MAX, Repository
from core.db.tables import Member
from core.limits import AUTOCOMPLETE_CHOICES_MAX
from members.models import DiscordMember

if TYPE_CHECKING:
    import discord

    from typing_extensions import Any

    from sqlalchemy.engine import Row


SEARCH_DISTANCE_MAX = 3
SEARCH_RESULTS_MAX = 5


class MemberRepository(Repository):
    @staticmethod
    def _record_build(member: discord.Member) -> Member:
        return Member(
            discord_id=member.id,
            name=member.name,
            display_name=member.display_name,
            nickname=member.nick,
            role_id=member.top_role.id,
            bot=member.bot,
            created_at=member.created_at,
            joined_at=member.joined_at,
        )

    @staticmethod
    def _values_build(
        member: discord.Member,
        previous_name: str | None,
        previous_nickname: str | None,
        updated_at: datetime
    ) -> dict[str, Any]:
        values = {
            'name': member.name,
            'display_name': member.display_name,
            'nickname': member.nick,
            'role_id': member.top_role.id,
            'updated_at': updated_at,
        }

        if previous_name is not None:
            values['previous_name'] = func.array_prepend(
                cast(previous_name, TEXT), Member.previous_name
            )

        if previous_nickname is not None:
            values['previous_nickname'] = func.array_prepend(
                cast(previous_nickname, TEXT), Member.previous_nickname
            )

        return values

    async def ban(self, discord_id: int) -> None:
        banned_at = datetime.now(UTC)

        statement = (
            update(Member)
            .where(Member.discord_id == discord_id)
            .values(banned_at=banned_at)
        )

        await self._execute(statement)

    async def ban_many(self, discord_ids: list[int]) -> None:
        banned_at = datetime.now(UTC)

        statement = (
            update(Member)
            .where(Member.discord_id.in_(discord_ids))
            .values(banned_at=banned_at)
        )

        await self._execute(statement)

    async def create(self, member: discord.Member) -> None:
        record = self._record_build(member)
        await self._add(record)

    async def create_many(self, members: list[discord.Member]) -> None:
        async with self._session_maker() as session:
            for member in members:
                record = self._record_build(member)
                session.add(record)

            await session.commit()

    async def created_get(self, discord_id: int) -> DiscordMember | None:
        query = (
            select(Member.display_name, Member.created_at)
            .where(Member.discord_id == discord_id)
        )

        row = await self._first(query)

        if row is None:
            return None

        return DiscordMember(
            display_name=row.display_name,
            created_at=row.created_at,
        )

    async def display_names_search(self, current: str) -> list[str]:
        pattern = f'%{current}%'

        query = (
            select(Member.display_name)
            .where(Member.display_name.ilike(pattern))
            .where(Member.removed_at.is_(None))
            .order_by(Member.display_name)
            .limit(AUTOCOMPLETE_CHOICES_MAX)
        )

        return await self._scalars(query)

    async def identifier_get(self, discord_id: int) -> int | None:
        query = select(Member.discord_id).where(Member.discord_id == discord_id)
        return await self._scalar(query)

    async def is_banned(self, discord_id: int) -> bool:
        query = (
            select(Member)
            .where(Member.discord_id == discord_id)
            .where(Member.banned_at.isnot(None))
        )

        row = await self._scalar(query)
        return row is not None

    async def is_removed(self, discord_id: int) -> bool:
        query = (
            select(Member)
            .where(Member.discord_id == discord_id)
            .where(Member.removed_at.isnot(None))
        )

        row = await self._scalar(query)
        return row is not None

    async def joined_get(self, discord_id: int) -> DiscordMember | None:
        query = (
            select(Member.display_name, Member.joined_at)
            .where(Member.discord_id == discord_id)
        )

        row = await self._first(query)

        if row is None:
            return None

        return DiscordMember(
            display_name=row.display_name,
            joined_at=row.joined_at,
        )

    async def member_count(self) -> int:
        query = select(func.count(Member.discord_id))
        return await self._scalar(query)

    async def name_append(self, before: discord.Member, after: discord.Member) -> None:
        updated_at = datetime.now(UTC)

        statement = (
            update(Member)
            .where(Member.discord_id == after.id)
            .values(
                name=after.name,
                previous_name=func.array_prepend(cast(before.name, TEXT), Member.previous_name),
                display_name=after.display_name,
                updated_at=updated_at,
            )
        )

        await self._execute(statement)

    async def name_get(self, discord_id: int) -> str | None:
        query = select(Member.name).where(Member.discord_id == discord_id)
        return await self._scalar(query)

    async def nickname_append(self, before: discord.Member, after: discord.Member) -> None:
        updated_at = datetime.now(UTC)

        statement = (
            update(Member)
            .where(Member.discord_id == after.id)
            .values(
                nickname=after.nick,
                previous_nickname=func.array_prepend(
                    cast(before.nick, TEXT), Member.previous_nickname
                ),
                display_name=after.display_name,
                updated_at=updated_at,
            )
        )

        await self._execute(statement)

    async def nickname_count(self) -> int:
        query = select(func.count(Member.nickname))
        return await self._scalar(query)

    async def nickname_update(self, after: discord.Member) -> None:
        updated_at = datetime.now(UTC)

        statement = (
            update(Member)
            .where(Member.discord_id == after.id)
            .values(
                nickname=after.nick,
                display_name=after.display_name,
                updated_at=updated_at,
            )
        )

        await self._execute(statement)

    async def previous_name_prepend(self, discord_id: int, name: str) -> None:
        statement = (
            update(Member)
            .where(Member.discord_id == discord_id)
            .values(
                previous_name=func.array_prepend(cast(name, TEXT), Member.previous_name),
            )
        )

        await self._execute(statement)

    async def previous_nickname_prepend(self, discord_id: int, nickname: str) -> None:
        statement = (
            update(Member)
            .where(Member.discord_id == discord_id)
            .values(
                previous_nickname=func.array_prepend(
                    cast(nickname, TEXT), Member.previous_nickname
                ),
            )
        )

        await self._execute(statement)

    async def previous_record_get(self, discord_id: int) -> DiscordMember | None:
        query = (
            select(Member.name, Member.nickname, Member.removed_at, Member.banned_at)
            .where(Member.discord_id == discord_id)
        )

        row = await self._first(query)

        if row is None:
            return None

        return DiscordMember(
            name=row.name,
            nickname=row.nickname,
            removed_at=row.removed_at,
            banned_at=row.banned_at,
        )

    async def profile_synchronize(
        self,
        updates: list[tuple[discord.Member, str | None, str | None]]
    ) -> None:
        updated_at = datetime.now(UTC)

        async with self._session_maker() as session:
            for member, previous_name, previous_nickname in updates:
                values = self._values_build(
                    member,
                    previous_name,
                    previous_nickname,
                    updated_at
                )

                await session.execute(
                    update(Member)
                    .where(Member.discord_id == member.id)
                    .values(**values)
                )

            await session.commit()

    async def profile_update(
        self,
        member: discord.Member,
        *,
        removed_at: datetime | None,
        banned_at: datetime | None,
    ) -> None:
        moment = datetime.now(UTC)

        statement = (
            update(Member)
            .where(Member.discord_id == member.id)
            .values(
                name=member.name,
                display_name=member.display_name,
                nickname=member.nick,
                role_id=member.top_role.id,
                joined_at=moment,
                updated_at=moment,
                removed_at=removed_at,
                banned_at=banned_at,
            )
        )

        await self._execute(statement)

    async def record_get(self, discord_id: int) -> DiscordMember | None:
        query = select(Member).where(Member.discord_id == discord_id)
        record = await self._scalar(query)

        if record is None:
            return None

        return DiscordMember(
            identifier=record.discord_id,
            name=record.name,
            display_name=record.display_name,
            nickname=record.nickname,
            role_identifier=record.role_id,
            previous_name=record.previous_name,
            previous_nickname=record.previous_nickname,
            created_at=record.created_at,
            joined_at=record.joined_at,
            updated_at=record.updated_at,
        )

    async def records_all(self) -> dict[int, DiscordMember]:
        query = select(Member).limit(RECORDS_MAX + 1)
        rows = await self._scalars(query)

        records = self._bounded(rows, 'MemberRepository.records_all')

        return {
            record.discord_id: DiscordMember(
                identifier=record.discord_id,
                name=record.name,
                display_name=record.display_name,
                nickname=record.nickname,
                role_identifier=record.role_id,
                bot=record.bot,
                removed_at=record.removed_at,
                banned_at=record.banned_at,
            )
            for record in records
        }

    async def remove(self, discord_id: int) -> None:
        removed_at = datetime.now(UTC)

        statement = (
            update(Member)
            .where(Member.discord_id == discord_id)
            .values(removed_at=removed_at)
        )

        await self._execute(statement)

    async def remove_many(self, discord_ids: list[int]) -> None:
        removed_at = datetime.now(UTC)

        statement = (
            update(Member)
            .where(Member.discord_id.in_(discord_ids))
            .values(removed_at=removed_at)
        )

        await self._execute(statement)

    async def restore(self, discord_id: int) -> None:
        statement = (
            update(Member)
            .where(Member.discord_id == discord_id)
            .values(removed_at=None)
        )

        await self._execute(statement)

    async def restore_many(
        self,
        restores: list[tuple[discord.Member, str | None, str | None]]
    ) -> None:
        updated_at = datetime.now(UTC)

        async with self._session_maker() as session:
            for member, previous_name, previous_nickname in restores:
                values = self._values_build(
                    member,
                    previous_name,
                    previous_nickname,
                    updated_at
                )

                values['joined_at'] = member.joined_at
                values['removed_at'] = None
                values['banned_at'] = None

                await session.execute(
                    update(Member)
                    .where(Member.discord_id == member.id)
                    .values(**values)
                )

            await session.commit()

    async def role_identifiers_get(self) -> dict[int, int | None]:
        query = select(Member.discord_id, Member.role_id).limit(RECORDS_MAX + 1)
        results = await self._all(query)

        rows = self._bounded(results, 'MemberRepository.role_identifiers_get')

        return {
            row.discord_id: row.role_id
            for row in rows
        }

    async def role_references_clear(self, role_identifiers: list[int]) -> None:
        statement = (
            update(Member)
            .where(Member.role_id.in_(role_identifiers))
            .values(role_id=None)
        )

        await self._execute(statement)

    async def role_synchronize(self, assignments: list[tuple[int, int]]) -> None:
        updated_at = datetime.now(UTC)

        async with self._session_maker() as session:
            for discord_id, role_identifier in assignments:
                await session.execute(
                    update(Member)
                    .where(Member.discord_id == discord_id)
                    .values(
                        role_id=role_identifier,
                        updated_at=updated_at,
                    )
                )

            await session.commit()

    async def role_update(self, after: discord.Member) -> None:
        updated_at = datetime.now(UTC)

        statement = (
            update(Member)
            .where(Member.discord_id == after.id)
            .values(
                role_id=after.top_role.id,
                updated_at=updated_at,
            )
        )

        await self._execute(statement)

    async def search(self, name: str) -> list[Row[Any]]:
        condition = (
            (func.levenshtein(func.lower(Member.display_name), name) <= SEARCH_DISTANCE_MAX) |
            (func.levenshtein(func.lower(Member.name), name) <= SEARCH_DISTANCE_MAX) |
            (func.levenshtein(func.lower(Member.nickname), name) <= SEARCH_DISTANCE_MAX)
        )

        query = (
            select(Member.discord_id, Member.display_name, Member.name, Member.nickname)
            .where(condition)
            .limit(SEARCH_RESULTS_MAX)
        )

        return await self._all(query)

    async def unban(self, discord_id: int) -> None:
        statement = (
            update(Member)
            .where(Member.discord_id == discord_id)
            .values(banned_at=None)
        )

        await self._execute(statement)

    async def unban_many(self, discord_ids: list[int]) -> None:
        statement = (
            update(Member)
            .where(Member.discord_id.in_(discord_ids))
            .values(banned_at=None)
        )

        await self._execute(statement)
