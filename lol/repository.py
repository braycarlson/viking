from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from rapidfuzz import process
from sqlalchemy import select

from core.db.lol import Champion, Item, Spell, Version
from core.db.repository import Repository

if TYPE_CHECKING:
    from collections.abc import Collection


class LolRepository(Repository):
    async def champion_get(self, champion_name: str) -> Champion | None:
        matched = await self.champion_search(champion_name)

        if matched is None:
            return None

        query = (
            select(Champion)
            .where(Champion.name == matched)
            .order_by(Champion.id)
            .limit(1)
        )

        return await self._scalar(query)

    async def champion_name_get(self, champion_identifier: int) -> str | None:
        query = select(Champion.name).where(Champion.id == str(champion_identifier))
        return await self._scalar(query)

    async def champion_names_get(self) -> list[str]:
        query = select(Champion.name)
        return await self._scalars(query)

    async def champion_search(self, champion_name: str) -> str | None:
        champion_names = await self.champion_names_get()

        if not champion_names:
            return None

        match, _, _ = process.extractOne(
            champion_name,
            champion_names
        )

        return match

    async def item_names_get(self, item_identifiers: Collection[str]) -> dict[str, str]:
        if not item_identifiers:
            return {}

        query = select(Item.id, Item.name).where(Item.id.in_(item_identifiers))
        rows = await self._all(query)

        return {
            row.id: row.name
            for row in rows
        }

    async def spell_get(self, spell_name: str) -> Spell | None:
        matched = await self.spell_search(spell_name)

        if matched is None:
            return None

        query = (
            select(Spell)
            .where(Spell.name == matched)
            .order_by(Spell.id)
            .limit(1)
        )

        return await self._scalar(query)

    async def spell_names_get(self) -> list[str]:
        query = select(Spell.name)
        return await self._scalars(query)

    async def spell_search(self, spell_name: str) -> str | None:
        spell_names = await self.spell_names_get()

        if not spell_names:
            return None

        match, _, _ = process.extractOne(
            spell_name,
            spell_names
        )

        return match

    async def spell_version_get(self) -> str | None:
        query = select(Version.summoner).where(Version.id == 1)
        return await self._scalar(query)
