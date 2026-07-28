from __future__ import annotations

from datetime import datetime, UTC
from typing_extensions import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from core.db.repository import Repository
from core.db.tables import Sound

if TYPE_CHECKING:
    from typing_extensions import Any

    from sqlalchemy.engine import Row


class SoundRepository(Repository):
    async def create(self, name: str, created_by: int) -> None:
        created_at = datetime.now(UTC)

        record = Sound(
            name=name,
            created_by=created_by,
            created_at=created_at,
        )

        await self._add(record)

    async def create_many(self, names: list[str], created_by: int) -> None:
        created_at = datetime.now(UTC)

        async with self._session_maker() as session:
            for name in names:
                record = Sound(
                    name=name,
                    created_by=created_by,
                    created_at=created_at,
                )

                session.add(record)

            await session.commit()

    async def creator_names_get(self, created_by: int) -> list[str]:
        query = select(Sound.name).where(Sound.created_by == created_by)
        return await self._scalars(query)

    async def delete(self, name: str) -> None:
        statement = delete(Sound).where(Sound.name == name)
        await self._execute(statement)

    async def owned_identifier_get(self, name: str, created_by: int) -> int | None:
        query = (
            select(Sound.id)
            .where(Sound.created_by == created_by)
            .where(Sound.name == name)
            .limit(1)
        )

        return await self._scalar(query)

    async def rename(self, identifier: int, name: str) -> None:
        statement = (
            update(Sound)
            .where(Sound.id == identifier)
            .values(name=name)
        )

        await self._execute(statement)

    async def tag_append(self, identifier: int, tag: str) -> None:
        statement = (
            update(Sound)
            .where(Sound.id == identifier)
            .values(tags=func.array_append(Sound.tags, tag))
        )

        await self._execute(statement)

    async def tag_remove(self, identifier: int, tag: str) -> None:
        statement = (
            update(Sound)
            .where(Sound.id == identifier)
            .values(tags=func.array_remove(Sound.tags, tag))
        )

        await self._execute(statement)

    async def tagged_get(self) -> list[Row[Any]]:
        query = select(Sound.name, Sound.tags).where(Sound.tags.isnot(None))
        return await self._all(query)

    async def tags_get(self, name: str) -> list[str] | None:
        query = select(Sound.tags).where(Sound.name == name)
        return await self._scalar(query)

    async def tags_row_get(self, name: str) -> Row[Any] | None:
        query = select(Sound.id, Sound.tags).where(Sound.name == name)
        return await self._first(query)
