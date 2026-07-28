from __future__ import annotations

from dataclasses import dataclass
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    import discord

    from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class PendingPresence:
    guild_identifier: int
    moment: datetime
    before: discord.Member
    after: discord.Member


@dataclass(frozen=True, kw_only=True)
class PendingVoice:
    guild_identifier: int
    moment: datetime
    member: discord.Member
    before: discord.VoiceState
    after: discord.VoiceState
