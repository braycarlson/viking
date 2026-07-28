from __future__ import annotations

import discord

from datetime import timedelta
from typing_extensions import TYPE_CHECKING

from activity.enums import ActivityType
from activity.models import (
    FriendEdge,
    FriendNode,
    FriendshipGraph,
    LastSeen,
    MemberWrapped,
)
from activity.repository import (
    ActivitySessionRepository,
    ListeningSessionRepository,
    StatusSessionRepository,
    VoiceSessionRepository,
)

if TYPE_CHECKING:
    from datetime import datetime

    from activity.models import PairOverlap
    from bot import Viking


TRACKABLE = {activity_type.value for activity_type in ActivityType}

WRAPPED_ARTISTS_MAX = 3
WRAPPED_CHANNELS_MAX = 1
WRAPPED_GAMES_MAX = 3

GAME_WEIGHT = 0.3
MUSIC_WEIGHT = 0.1
VOICE_WEIGHT = 0.6

GRAPH_EDGES_MAX = 70
GRAPH_NEIGHBOURS_MAX = 12
GRAPH_NODES_MAX = 24
PAIR_SAMPLE_MAX = 600


class ActivityEvent:
    def __init__(self, viking: Viking) -> None:
        self.viking = viking

    @property
    def activities(self) -> ActivitySessionRepository:
        return ActivitySessionRepository(self.viking.guild.session)

    @property
    def listening(self) -> ListeningSessionRepository:
        return ListeningSessionRepository(self.viking.guild.session)

    @property
    def status(self) -> StatusSessionRepository:
        return StatusSessionRepository(self.viking.guild.session)

    @property
    def voice(self) -> VoiceSessionRepository:
        return VoiceSessionRepository(self.viking.guild.session)

    async def _activity_synchronize(
        self,
        before: discord.Member,
        after: discord.Member,
        moment: datetime
    ) -> None:
        before_activities = {
            self._key(activity): activity
            for activity in before.activities
            if self._trackable(activity)
        }

        after_activities = {
            self._key(activity): activity
            for activity in after.activities
            if self._trackable(activity)
        }

        for key in before_activities.keys() - after_activities.keys():
            activity_type, name = key
            await self.activities.close(after.id, activity_type, name, moment)

        for key in after_activities.keys() - before_activities.keys():
            await self.activities.open(after.id, after_activities[key], moment)

        for key in before_activities.keys() & after_activities.keys():
            await self.activities.state_sync(after.id, after_activities[key], moment)

    @staticmethod
    def _degree(edges: dict[tuple[int, int], float]) -> dict[int, float]:
        degree = {}

        for (source, target), score in edges.items():
            degree[source] = degree.get(source, 0.0) + score
            degree[target] = degree.get(target, 0.0) + score

        return degree

    def _graph_build(
        self,
        edges: dict[tuple[int, int], float],
        center: int | None
    ) -> FriendshipGraph:
        if not edges:
            return FriendshipGraph(nodes=[], edges=[], center=center)

        peak = max(edges.values())
        degree = self._degree(edges)
        degree_peak = max(degree.values())

        nodes = [
            FriendNode(discord_id=node_identifier, weight=value / degree_peak)
            for node_identifier, value in degree.items()
        ]

        friend_edges = [
            FriendEdge(source=source, target=target, weight=score / peak)
            for (source, target), score in edges.items()
        ]

        return FriendshipGraph(nodes=nodes, edges=friend_edges, center=center)

    def _graph_ego(
        self,
        blended: dict[tuple[int, int], float],
        center: int
    ) -> FriendshipGraph:
        neighbours = {}

        for (source, target), score in blended.items():
            if source == center:
                neighbours[target] = score

            if target == center:
                neighbours[source] = score

        if not neighbours:
            return FriendshipGraph(nodes=[], edges=[], center=center)

        ranked = sorted(neighbours, key=neighbours.get, reverse=True)
        keep = set(ranked[:GRAPH_NEIGHBOURS_MAX])
        keep.add(center)

        edges = {
            key: score
            for key, score in blended.items()
            if key[0] in keep and key[1] in keep
        }

        return self._graph_build(edges, center)

    def _graph_server(self, blended: dict[tuple[int, int], float]) -> FriendshipGraph:
        degree = self._degree(blended)

        ranked = sorted(degree, key=degree.get, reverse=True)
        keep = set(ranked[:GRAPH_NODES_MAX])

        edges = {
            key: score
            for key, score in blended.items()
            if key[0] in keep and key[1] in keep
        }

        ranked_edges = sorted(edges.items(), key=lambda item: item[1], reverse=True)
        edges = dict(ranked_edges[:GRAPH_EDGES_MAX])

        return self._graph_build(edges, None)

    @staticmethod
    def _key(activity: discord.BaseActivity) -> tuple[str, str | None]:
        return (activity.type.name, activity.name)

    async def _listening_synchronize(
        self,
        before: discord.Member,
        after: discord.Member,
        moment: datetime
    ) -> None:
        before_tracks = {
            activity.track_id
            for activity in before.activities
            if isinstance(activity, discord.Spotify)
        }

        after_spotify = {
            activity.track_id: activity
            for activity in after.activities
            if isinstance(activity, discord.Spotify)
        }

        if before_tracks - after_spotify.keys():
            await self.listening.close(after.id, moment)

        for track_id in after_spotify.keys() - before_tracks:
            await self.listening.open(after.id, after_spotify[track_id], moment)

    @staticmethod
    def _normalize(pairs: list[PairOverlap]) -> dict[tuple[int, int], float]:
        seconds = {
            (pair.source, pair.target): pair.duration.total_seconds()
            for pair in pairs
            if pair.duration is not None
        }

        peak = max(seconds.values(), default=0.0)

        if peak <= 0:
            return {}

        return {key: value / peak for key, value in seconds.items()}

    def _pairs_blend(
        self,
        voice: list[PairOverlap],
        games: list[PairOverlap],
        music: list[PairOverlap]
    ) -> dict[tuple[int, int], float]:
        voice_normalized = self._normalize(voice)
        game_normalized = self._normalize(games)
        music_normalized = self._normalize(music)

        keys = voice_normalized.keys() | game_normalized.keys() | music_normalized.keys()

        blended = {}

        for key in keys:
            score = (
                VOICE_WEIGHT * voice_normalized.get(key, 0.0)
                + GAME_WEIGHT * game_normalized.get(key, 0.0)
                + MUSIC_WEIGHT * music_normalized.get(key, 0.0)
            )

            if score > 0:
                blended[key] = score

        return blended

    async def _status_synchronize(
        self,
        before: discord.Member,
        after: discord.Member,
        moment: datetime
    ) -> None:
        offline = discord.Status.offline

        before_key = (
            before.status,
            before.desktop_status is not offline,
            before.web_status is not offline,
            before.mobile_status is not offline,
        )

        after_key = (
            after.status,
            after.desktop_status is not offline,
            after.web_status is not offline,
            after.mobile_status is not offline,
        )

        if before_key == after_key:
            return

        await self.status.close(after.id, moment)

        if after.status is not offline:
            await self.status.open(after, moment)

    @staticmethod
    def _trackable(activity: discord.BaseActivity) -> bool:
        return not isinstance(activity, discord.Spotify) and activity.type.name in TRACKABLE

    @staticmethod
    def _voice_key(state: discord.VoiceState) -> int | None:
        if state.channel is None:
            return None

        return state.channel.id

    @staticmethod
    def _voice_state_key(state: discord.VoiceState) -> tuple[bool, ...]:
        return (
            state.self_stream,
            state.self_video,
            state.self_mute,
            state.self_deaf,
            state.mute,
            state.deaf,
            state.suppress,
            state.afk,
        )

    async def graph_friendship(self, center: int | None = None) -> FriendshipGraph:
        voice = await self.voice.pair_overlap(PAIR_SAMPLE_MAX)
        games = await self.activities.pair_overlap(PAIR_SAMPLE_MAX)
        music = await self.listening.pair_overlap(PAIR_SAMPLE_MAX)

        blended = self._pairs_blend(voice, games, music)

        if not blended:
            return FriendshipGraph(nodes=[], edges=[], center=center)

        if center is None:
            return self._graph_server(blended)

        return self._graph_ego(blended, center)

    async def member_last_seen(self, discord_id: int) -> LastSeen:
        status = await self.status.member_last(discord_id)
        game = await self.activities.member_last(discord_id)
        voice = await self.voice.member_last(discord_id)

        return LastSeen(status=status, game=game, voice=voice)

    async def member_wrapped(self, discord_id: int) -> MemberWrapped:
        games = await self.activities.member_games(discord_id, WRAPPED_GAMES_MAX)
        artists = await self.listening.member_artists(discord_id, WRAPPED_ARTISTS_MAX)
        channels = await self.voice.member_voice(discord_id, WRAPPED_CHANNELS_MAX)
        longest = await self.activities.member_longest(discord_id)
        game_time = await self.activities.member_total(discord_id)
        voice_time = await self.voice.member_total(discord_id)
        online_time = await self.status.member_total(discord_id)

        zero = timedelta()

        if channels:
            channel = channels[0]
        else:
            channel = None

        return MemberWrapped(
            games=games,
            artists=artists,
            channel=channel,
            longest=longest,
            game_time=game_time or zero,
            voice_time=voice_time or zero,
            online_time=online_time or zero,
        )

    async def presence_update(
        self,
        before: discord.Member,
        after: discord.Member,
        moment: datetime
    ) -> None:
        await self._status_synchronize(before, after, moment)
        await self._listening_synchronize(before, after, moment)
        await self._activity_synchronize(before, after, moment)

    async def shutdown(self, moment: datetime) -> None:
        await self.activities.dangling_close(moment)
        await self.listening.dangling_close(moment)
        await self.voice.dangling_close(moment)
        await self.status.dangling_close(moment)

    async def snapshot(self, guild: discord.Guild, moment: datetime) -> None:
        await self.activities.dangling_zero()
        await self.listening.dangling_zero()
        await self.voice.dangling_zero()
        await self.status.dangling_zero()

        offline = discord.Status.offline

        for member in guild.members:
            if member.status is not offline:
                await self.status.open(member, moment)

            for activity in member.activities:
                if isinstance(activity, discord.Spotify):
                    await self.listening.open(member.id, activity, moment)
                    continue

                if self._trackable(activity):
                    await self.activities.open(member.id, activity, moment)

            voice_state = member.voice

            if voice_state is not None and voice_state.channel is not None:
                await self.voice.open(member, voice_state, moment)

    async def voice_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
        moment: datetime
    ) -> None:
        before_channel = self._voice_key(before)
        after_channel = self._voice_key(after)

        if before_channel != after_channel:
            if before_channel is not None:
                await self.voice.close(member.id, moment)

            if after_channel is not None:
                await self.voice.open(member, after, moment)

            return

        if after_channel is None:
            return

        if self._voice_state_key(before) == self._voice_state_key(after):
            return

        await self.voice.state_sync(member.id, after, moment)
