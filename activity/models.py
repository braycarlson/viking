from __future__ import annotations

import msgspec

from datetime import datetime, timedelta


class GameStat(msgspec.Struct):
    name: str
    duration: timedelta
    sessions: int


class ArtistStat(msgspec.Struct):
    artist: str
    duration: timedelta
    sessions: int


class TrackStat(msgspec.Struct):
    track: str
    artist: str
    duration: timedelta
    sessions: int


class ChannelStat(msgspec.Struct):
    channel_id: int
    channel_name: str | None
    duration: timedelta
    sessions: int


class MemberStat(msgspec.Struct):
    discord_id: int
    duration: timedelta
    sessions: int


class DeviceStat(msgspec.Struct):
    desktop: timedelta | None
    web: timedelta | None
    mobile: timedelta | None


class NowPlaying(msgspec.Struct):
    discord_id: int
    name: str
    started_at: datetime


class LongestSession(msgspec.Struct):
    name: str | None
    duration: timedelta


class LastActivity(msgspec.Struct):
    name: str | None
    started_at: datetime
    ended_at: datetime | None


class LastVoice(msgspec.Struct):
    channel_name: str | None
    started_at: datetime
    ended_at: datetime | None


class LastStatus(msgspec.Struct):
    status: str
    started_at: datetime
    ended_at: datetime | None


class LastSeen(msgspec.Struct):
    status: LastStatus | None
    game: LastActivity | None
    voice: LastVoice | None


class MemberWrapped(msgspec.Struct):
    games: list[GameStat]
    artists: list[ArtistStat]
    channel: ChannelStat | None
    longest: LongestSession | None
    game_time: timedelta
    voice_time: timedelta
    online_time: timedelta


class PairOverlap(msgspec.Struct):
    source: int
    target: int
    duration: timedelta | None
    sessions: int


class FriendNode(msgspec.Struct):
    discord_id: int
    weight: float


class FriendEdge(msgspec.Struct):
    source: int
    target: int
    weight: float


class FriendshipGraph(msgspec.Struct):
    nodes: list[FriendNode]
    edges: list[FriendEdge]
    center: int | None
