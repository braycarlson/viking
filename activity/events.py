from __future__ import annotations

import discord

from dataclasses import dataclass
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class PendingPresence:
    guild_identifier: int
    moment: datetime
    before: PresenceSnapshot
    after: PresenceSnapshot


@dataclass(frozen=True, kw_only=True)
class PendingVoice:
    guild_identifier: int
    moment: datetime
    before: VoiceSnapshot
    after: VoiceSnapshot


@dataclass(frozen=True, kw_only=True)
class PresenceSnapshot:
    discord_id: int
    status: str
    desktop: bool
    web: bool
    mobile: bool
    activities: tuple[discord.BaseActivity, ...]

    @classmethod
    def capture(cls, member: discord.Member) -> PresenceSnapshot:
        offline = discord.Status.offline

        return cls(
            discord_id=member.id,
            status=member.status.value,
            desktop=member.desktop_status is not offline,
            web=member.web_status is not offline,
            mobile=member.mobile_status is not offline,
            activities=tuple(member.activities),
        )

    @property
    def key(self) -> tuple[str, bool, bool, bool]:
        return (self.status, self.desktop, self.web, self.mobile)

    @property
    def online(self) -> bool:
        return self.status != discord.Status.offline.value


@dataclass(frozen=True, kw_only=True)
class VoiceSnapshot:
    discord_id: int
    channel_id: int | None
    channel_name: str | None
    session_id: str | None
    streaming: bool
    video: bool
    self_mute: bool
    self_deaf: bool
    server_mute: bool
    server_deaf: bool
    suppress: bool
    afk: bool

    @classmethod
    def capture(cls, member: discord.Member, state: discord.VoiceState) -> VoiceSnapshot:
        channel = state.channel

        if channel is None:
            channel_id = None
            channel_name = None
        else:
            channel_id = channel.id
            channel_name = channel.name

        return cls(
            discord_id=member.id,
            channel_id=channel_id,
            channel_name=channel_name,
            session_id=state.session_id,
            streaming=state.self_stream,
            video=state.self_video,
            self_mute=state.self_mute,
            self_deaf=state.self_deaf,
            server_mute=state.mute,
            server_deaf=state.deaf,
            suppress=state.suppress,
            afk=state.afk,
        )

    @property
    def key(self) -> tuple[bool, ...]:
        return (
            self.streaming,
            self.video,
            self.self_mute,
            self.self_deaf,
            self.server_mute,
            self.server_deaf,
            self.suppress,
            self.afk,
        )

    @property
    def state(self) -> dict[str, bool]:
        return {
            'streaming': self.streaming,
            'video': self.video,
            'self_mute': self.self_mute,
            'self_deaf': self.self_deaf,
            'server_mute': self.server_mute,
            'server_deaf': self.server_deaf,
            'suppress': self.suppress,
            'afk': self.afk,
        }
