from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from discord import app_commands
from rapidfuzz import process

from core.db.registry import databases
from core.limits import AUTOCOMPLETE_CHOICES_MAX
from lol.repository import LolRepository

if TYPE_CHECKING:
    from discord import Interaction


def _choices(names: list[str], current: str) -> list[app_commands.Choice[str]]:
    if current:
        matches = process.extract(current, names, limit=AUTOCOMPLETE_CHOICES_MAX)
        selected = [match for match, _, _ in matches]
    else:
        selected = sorted(names)[:AUTOCOMPLETE_CHOICES_MAX]

    return [
        app_commands.Choice(name=name, value=name)
        for name in dict.fromkeys(selected)
    ]


async def champion_autocomplete(
    interaction: Interaction,  # noqa: ARG001
    current: str
) -> list[app_commands.Choice[str]]:
    repository = LolRepository(databases.lol.session)
    names = await repository.champion_names_get()

    return _choices(names, current)


async def spell_autocomplete(
    interaction: Interaction,  # noqa: ARG001
    current: str
) -> list[app_commands.Choice[str]]:
    repository = LolRepository(databases.lol.session)
    names = await repository.spell_names_get()

    return _choices(names, current)
