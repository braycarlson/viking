from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from discord import app_commands
from rapidfuzz import process

from core.limits import AUTOCOMPLETE_CHOICES_MAX

if TYPE_CHECKING:
    from discord import Interaction


async def sound_autocomplete(
    interaction: Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    viking = interaction.client

    default = viking.sound.joinpath('default')
    member = viking.sound.joinpath('member')

    names = sorted(
        path.stem
        for path in [*default.iterdir(), *member.iterdir()]
    )

    if current:
        matches = process.extract(current, names, limit=AUTOCOMPLETE_CHOICES_MAX)
        names = [match for match, _, _ in matches]
    else:
        names = names[:AUTOCOMPLETE_CHOICES_MAX]

    return [
        app_commands.Choice(name=name, value=name)
        for name in dict.fromkeys(names)
    ]
