from __future__ import annotations

from dataclasses import dataclass
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    import discord

    from collections.abc import Callable, Coroutine
    from typing_extensions import Any


@dataclass(frozen=True, kw_only=True)
class PendingRevert:
    action: str
    member: discord.Member
    revert_function: Callable[[discord.Member], Coroutine[Any, Any, None]]
