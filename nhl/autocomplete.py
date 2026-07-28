from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from discord import app_commands
from rapidfuzz import process

from core.limits import AUTOCOMPLETE_CHOICES_MAX
from nhl.api import TEAM_NAMES

if TYPE_CHECKING:
    from discord import Interaction


async def team_autocomplete(
    interaction: Interaction,  # noqa: ARG001
    current: str
) -> list[app_commands.Choice[str]]:
    names = list(TEAM_NAMES.keys())

    if current:
        matches = process.extract(current, names, limit=AUTOCOMPLETE_CHOICES_MAX)
        names = [match for match, _, _ in matches]
    else:
        names = names[:AUTOCOMPLETE_CHOICES_MAX]

    return [
        app_commands.Choice(name=name, value=name)
        for name in names
    ]
