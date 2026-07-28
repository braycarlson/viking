from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from sqlalchemy import delete, func, select

from core.db.repository import Repository
from core.db.tables import Hidden, Public

if TYPE_CHECKING:
    from typing_extensions import Any


LEVENSHTEIN_DISTANCE_MAX = 3
SUGGESTIONS_MAX = 5


class CommandRepository(Repository):
    async def _entries_create(
        self,
        model: type[Any],
        entries: list[tuple[str, list[str] | None]]
    ) -> None:
        async with self._session_maker() as session:
            for name, aliases in entries:
                record = model(name=name, aliases=aliases)
                session.add(record)

            await session.commit()

    async def hidden_create(self, entries: list[tuple[str, list[str] | None]]) -> None:
        await self._entries_create(Hidden, entries)

    async def hidden_names_get(self) -> list[str]:
        query = select(Hidden.name)
        return await self._scalars(query)

    async def public_create(self, entries: list[tuple[str, list[str] | None]]) -> None:
        await self._entries_create(Public, entries)

    async def public_delete(self, names: list[str]) -> None:
        statement = delete(Public).where(Public.name.in_(names))
        await self._execute(statement)

    async def public_names_get(self) -> list[str]:
        query = select(Public.name)
        return await self._scalars(query)

    async def suggestions_get(self, invoked_with: str) -> list[str]:
        query = (
            select(Public.name)
            .where(func.levenshtein(Public.name, invoked_with) <= LEVENSHTEIN_DISTANCE_MAX)
            .limit(SUGGESTIONS_MAX)
        )

        return await self._scalars(query)
