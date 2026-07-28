from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from core.db.repository import RECORDS_MAX, Repository
from core.db.tables import Role
from core.limits import AUTOCOMPLETE_CHOICES_MAX
from roles.models import DiscordRole, DiscordRoleError

if TYPE_CHECKING:
    import discord

    from typing_extensions import Any


class RoleRepository(Repository):
    @staticmethod
    def _record_build(role: discord.Role) -> Role:
        return Role(
            id=role.id,
            name=role.name,
            colour=str(role.colour),
            hoist=role.hoist,
            position=role.position,
            managed=role.managed,
            mentionable=role.mentionable,
            is_default=role.is_default(),
            created_at=role.created_at,
        )

    @staticmethod
    def _values_build(role: discord.Role) -> dict[str, Any]:
        return {
            'name': role.name,
            'colour': str(role.colour),
            'hoist': role.hoist,
            'position': role.position,
            'managed': role.managed,
            'mentionable': role.mentionable,
            'is_default': role.is_default(),
            'created_at': role.created_at,
        }

    async def create(self, role: discord.Role) -> None:
        record = self._record_build(role)
        await self._add(record)

    async def create_many(self, roles: list[discord.Role]) -> None:
        async with self._session_maker() as session:
            for role in roles:
                record = self._record_build(role)
                session.add(record)

            await session.commit()

    async def delete(self, role_identifier: int) -> None:
        statement = delete(Role).where(Role.id == role_identifier)
        await self._execute(statement)

    async def delete_many(self, role_identifiers: list[int]) -> None:
        statement = delete(Role).where(Role.id.in_(role_identifiers))
        await self._execute(statement)

    async def identifier_resolve(self, identifier: str) -> int:
        try:
            role_identifier = int(identifier)
        except ValueError:
            return await self.name_resolve(identifier)
        else:
            query = select(Role.id).where(Role.id == role_identifier)
            row = await self._scalar(query)

            if row is None:
                message = f'No role is stored with the ID: {role_identifier}'
                raise DiscordRoleError(message)

            return row

    async def name_exists(self, name: str) -> bool:
        query = select(Role.id).where(func.lower(Role.name) == name.lower())
        row = await self._scalar(query)

        return row is not None

    async def name_get(self, role_identifier: int) -> str | None:
        query = select(Role.name).where(Role.id == role_identifier)
        return await self._scalar(query)

    async def name_resolve(self, name: str) -> int:
        query = select(Role.id).where(func.lower(Role.name) == name.lower())
        row = await self._scalar(query)

        if row is None:
            message = f'No role is stored with the name: {name}'
            raise DiscordRoleError(message)

        return row

    async def names_search(self, current: str) -> list[str]:
        pattern = f'%{current}%'

        query = (
            select(Role.name)
            .where(Role.name.ilike(pattern))
            .order_by(Role.name)
            .limit(AUTOCOMPLETE_CHOICES_MAX)
        )

        return await self._scalars(query)

    async def record_get(self, role_identifier: int) -> DiscordRole | None:
        query = select(Role).where(Role.id == role_identifier)
        row = await self._first(query)

        if row is None:
            return None

        record = row[0]

        return DiscordRole(
            identifier=record.id,
            name=record.name,
            colour=record.colour,
            hoist=record.hoist,
            position=record.position,
            managed=record.managed,
            mentionable=record.mentionable,
            is_default=record.is_default,
            created_at=record.created_at,
        )

    async def records_all(self) -> dict[int, DiscordRole]:
        query = select(Role).limit(RECORDS_MAX + 1)
        rows = await self._scalars(query)

        records = self._bounded(rows, 'RoleRepository.records_all')

        return {
            record.id: DiscordRole(
                identifier=record.id,
                name=record.name,
                colour=record.colour,
                hoist=record.hoist,
                position=record.position,
                managed=record.managed,
                mentionable=record.mentionable,
                is_default=record.is_default,
                created_at=record.created_at,
            )
            for record in records
        }

    async def update(self, role: discord.Role) -> None:
        values = self._values_build(role)

        statement = (
            update(Role)
            .where(Role.id == role.id)
            .values(**values)
        )

        await self._execute(statement)

    async def update_many(self, roles: list[discord.Role]) -> None:
        async with self._session_maker() as session:
            for role in roles:
                values = self._values_build(role)

                statement = (
                    update(Role)
                    .where(Role.id == role.id)
                    .values(**values)
                )

                await session.execute(statement)

            await session.commit()
