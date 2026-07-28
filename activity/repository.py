from __future__ import annotations

import discord

from typing_extensions import ClassVar, TYPE_CHECKING

from sqlalchemy import and_, distinct, func, select, update
from sqlalchemy.orm import aliased

from activity.enums import ActivityType
from activity.models import (
    ArtistStat,
    ChannelStat,
    DeviceStat,
    GameStat,
    LastActivity,
    LastStatus,
    LastVoice,
    LongestSession,
    MemberStat,
    NowPlaying,
    PairOverlap,
    TrackStat,
)
from core.db.repository import Repository
from core.db.tables import (
    ActivitySession,
    ActivityState,
    ListeningSession,
    StatusSession,
    VoiceSession,
    VoiceState,
)

if TYPE_CHECKING:
    from datetime import datetime, timedelta
    from typing_extensions import Any

    from sqlalchemy.engine import Row
    from sqlalchemy.orm.util import AliasedClass


NOW_PLAYING_MAX = 100


class SessionRepository(Repository):
    model: ClassVar[type[Any] | None] = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        if cls.model is None:
            message = f'{cls.__name__} must define a model.'
            raise TypeError(message)

    @staticmethod
    def _overlap_condition(first: AliasedClass, second: AliasedClass) -> Any:
        first_range = func.tstzrange(first.started_at, first.ended_at)
        second_range = func.tstzrange(second.started_at, second.ended_at)

        return first_range.op('&&')(second_range)

    @staticmethod
    def _overlap_duration(first: AliasedClass, second: AliasedClass) -> Any:
        overlap = (
            func.least(first.ended_at, second.ended_at)
            - func.greatest(first.started_at, second.started_at)
        )

        return func.sum(overlap)

    @staticmethod
    def _pair_overlaps(rows: list[Row[Any]]) -> list[PairOverlap]:
        return [
            PairOverlap(
                source=row.source,
                target=row.target,
                duration=row.duration,
                sessions=row.sessions,
            )
            for row in rows
        ]

    async def dangling_close(self, ended_at: datetime) -> None:
        statement = (
            update(self.model)
            .where(self.model.ended_at.is_(None))
            .values(ended_at=ended_at)
        )

        await self._execute(statement)

    async def dangling_zero(self) -> None:
        statement = (
            update(self.model)
            .where(self.model.ended_at.is_(None))
            .values(ended_at=self.model.started_at)
        )

        await self._execute(statement)


class ActivitySessionRepository(SessionRepository):
    model = ActivitySession

    @staticmethod
    def _parent(activity: discord.Activity) -> dict[str, Any]:
        return {
            'type': activity.type.name,
            'name': activity.name,
            'url': getattr(activity, 'url', None),
            'application_id': getattr(activity, 'application_id', None),
            'platform': getattr(activity, 'platform', None),
            'declared_start': getattr(activity, 'start', None),
            'declared_end': getattr(activity, 'end', None),
        }

    @staticmethod
    def _state(activity: discord.Activity) -> dict[str, Any]:
        assets = getattr(activity, 'assets', None) or {}
        emoji = getattr(activity, 'emoji', None)
        party = getattr(activity, 'party', None) or {}
        size = party.get('size') or []
        buttons = getattr(activity, 'buttons', None) or None

        if emoji is None:
            emoji_text = None
        else:
            emoji_text = str(emoji)

        if len(size) > 0:
            party_size = size[0]
        else:
            party_size = None

        if len(size) > 1:
            party_max = size[1]
        else:
            party_max = None

        return {
            'details': getattr(activity, 'details', None),
            'state': getattr(activity, 'state', None),
            'emoji': emoji_text,
            'party_size': party_size,
            'party_max': party_max,
            'large_text': assets.get('large_text'),
            'small_text': assets.get('small_text'),
            'large_image': assets.get('large_image'),
            'small_image': assets.get('small_image'),
            'buttons': buttons,
        }

    async def close(
        self,
        discord_id: int,
        activity_type: str,
        name: str | None,
        ended_at: datetime
    ) -> None:
        conditions = [
            ActivitySession.discord_id == discord_id,
            ActivitySession.type == activity_type,
            ActivitySession.ended_at.is_(None),
        ]

        if name is None:
            condition = ActivitySession.name.is_(None)
        else:
            condition = ActivitySession.name == name

        conditions.append(condition)

        statement = update(ActivitySession).where(*conditions).values(ended_at=ended_at)
        await self._execute(statement)

    async def game_leaderboard(self, limit: int) -> list[GameStat]:
        duration = func.sum(ActivitySession.ended_at - ActivitySession.started_at)

        query = (
            select(
                ActivitySession.name,
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .where(ActivitySession.type == ActivityType.PLAYING)
            .where(ActivitySession.ended_at.isnot(None))
            .group_by(ActivitySession.name)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)

        return [
            GameStat(name=row.name, duration=row.duration, sessions=row.sessions)
            for row in rows
        ]

    async def member_games(self, discord_id: int, limit: int) -> list[GameStat]:
        duration = func.sum(ActivitySession.ended_at - ActivitySession.started_at)

        query = (
            select(
                ActivitySession.name,
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .where(ActivitySession.discord_id == discord_id)
            .where(ActivitySession.type == ActivityType.PLAYING)
            .where(ActivitySession.ended_at.isnot(None))
            .group_by(ActivitySession.name)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)

        return [
            GameStat(name=row.name, duration=row.duration, sessions=row.sessions)
            for row in rows
        ]

    async def member_last(self, discord_id: int) -> LastActivity | None:
        query = (
            select(
                ActivitySession.name,
                ActivitySession.started_at,
                ActivitySession.ended_at,
            )
            .where(ActivitySession.discord_id == discord_id)
            .where(ActivitySession.type == ActivityType.PLAYING)
            .order_by(ActivitySession.started_at.desc())
            .limit(1)
        )

        row = await self._first(query)

        if row is None:
            return None

        return LastActivity(
            name=row.name,
            started_at=row.started_at,
            ended_at=row.ended_at,
        )

    async def member_longest(self, discord_id: int) -> LongestSession | None:
        duration = ActivitySession.ended_at - ActivitySession.started_at

        query = (
            select(
                ActivitySession.name,
                duration.label('duration'),
            )
            .where(ActivitySession.discord_id == discord_id)
            .where(ActivitySession.type == ActivityType.PLAYING)
            .where(ActivitySession.ended_at.isnot(None))
            .order_by(duration.desc())
            .limit(1)
        )

        row = await self._first(query)

        if row is None:
            return None

        return LongestSession(name=row.name, duration=row.duration)

    async def member_total(self, discord_id: int) -> timedelta | None:
        duration = func.sum(ActivitySession.ended_at - ActivitySession.started_at)

        query = (
            select(duration)
            .where(ActivitySession.discord_id == discord_id)
            .where(ActivitySession.type == ActivityType.PLAYING)
            .where(ActivitySession.ended_at.isnot(None))
        )

        return await self._scalar(query)

    async def now_playing(self) -> list[NowPlaying]:
        query = (
            select(
                ActivitySession.discord_id,
                ActivitySession.name,
                ActivitySession.started_at,
            )
            .where(ActivitySession.type == ActivityType.PLAYING)
            .where(ActivitySession.ended_at.is_(None))
            .order_by(ActivitySession.started_at)
            .limit(NOW_PLAYING_MAX)
        )

        rows = await self._all(query)

        return [
            NowPlaying(
                discord_id=row.discord_id,
                name=row.name,
                started_at=row.started_at,
            )
            for row in rows
        ]

    async def open(
        self,
        discord_id: int,
        activity: discord.Activity,
        started_at: datetime
    ) -> None:
        parent = self._parent(activity)
        state = self._state(activity)

        await self.close(discord_id, parent['type'], parent['name'], started_at)

        async with self._session_maker() as session:
            record = ActivitySession(discord_id=discord_id, started_at=started_at, **parent)
            session.add(record)
            await session.flush()

            child = ActivityState(session_id=record.id, changed_at=started_at, **state)
            session.add(child)

            await session.commit()

    async def pair_overlap(self, limit: int) -> list[PairOverlap]:
        first = aliased(ActivitySession)
        second = aliased(ActivitySession)

        duration = self._overlap_duration(first, second)

        query = (
            select(
                first.discord_id.label('source'),
                second.discord_id.label('target'),
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .select_from(first)
            .join(
                second,
                and_(
                    first.name == second.name,
                    first.discord_id < second.discord_id,
                    self._overlap_condition(first, second),
                ),
            )
            .where(first.type == ActivityType.PLAYING)
            .where(second.type == ActivityType.PLAYING)
            .where(first.name.isnot(None))
            .where(first.ended_at.isnot(None))
            .where(second.ended_at.isnot(None))
            .group_by(first.discord_id, second.discord_id)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)
        return self._pair_overlaps(rows)

    async def state_sync(
        self,
        discord_id: int,
        activity: discord.Activity,
        moment: datetime
    ) -> None:
        conditions = [
            ActivitySession.discord_id == discord_id,
            ActivitySession.type == activity.type.name,
            ActivitySession.ended_at.is_(None),
        ]

        if activity.name is None:
            condition = ActivitySession.name.is_(None)
        else:
            condition = ActivitySession.name == activity.name

        conditions.append(condition)

        state = self._state(activity)

        async with self._session_maker() as session:
            open_id = await session.scalar(
                select(ActivitySession.id).where(*conditions)
            )

            if open_id is None:
                return

            statement = (
                select(
                    ActivityState.state,
                    ActivityState.party_size,
                    ActivityState.party_max,
                )
                .where(ActivityState.session_id == open_id)
                .order_by(ActivityState.changed_at.desc())
                .limit(1)
            )

            result = await session.execute(statement)
            latest = result.first()

            key = (state['state'], state['party_size'], state['party_max'])

            if latest is not None and (latest.state, latest.party_size, latest.party_max) == key:
                return

            child = ActivityState(session_id=open_id, changed_at=moment, **state)
            session.add(child)

            await session.commit()


class ListeningSessionRepository(SessionRepository):
    model = ListeningSession

    async def artist_leaderboard(self, limit: int) -> list[ArtistStat]:
        duration = func.sum(ListeningSession.ended_at - ListeningSession.started_at)

        query = (
            select(
                ListeningSession.artist,
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .where(ListeningSession.ended_at.isnot(None))
            .group_by(ListeningSession.artist)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)

        return [
            ArtistStat(artist=row.artist, duration=row.duration, sessions=row.sessions)
            for row in rows
        ]

    async def close(self, discord_id: int, ended_at: datetime) -> None:
        statement = (
            update(ListeningSession)
            .where(ListeningSession.discord_id == discord_id)
            .where(ListeningSession.ended_at.is_(None))
            .values(ended_at=ended_at)
        )

        await self._execute(statement)

    async def member_artists(self, discord_id: int, limit: int) -> list[ArtistStat]:
        duration = func.sum(ListeningSession.ended_at - ListeningSession.started_at)

        query = (
            select(
                ListeningSession.artist,
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .where(ListeningSession.discord_id == discord_id)
            .where(ListeningSession.ended_at.isnot(None))
            .group_by(ListeningSession.artist)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)

        return [
            ArtistStat(artist=row.artist, duration=row.duration, sessions=row.sessions)
            for row in rows
        ]

    async def member_tracks(self, discord_id: int, limit: int) -> list[TrackStat]:
        duration = func.sum(ListeningSession.ended_at - ListeningSession.started_at)

        query = (
            select(
                ListeningSession.track,
                ListeningSession.artist,
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .where(ListeningSession.discord_id == discord_id)
            .where(ListeningSession.ended_at.isnot(None))
            .group_by(ListeningSession.track, ListeningSession.artist)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)

        return [
            TrackStat(
                track=row.track,
                artist=row.artist,
                duration=row.duration,
                sessions=row.sessions,
            )
            for row in rows
        ]

    async def open(
        self,
        discord_id: int,
        spotify: discord.Spotify,
        started_at: datetime
    ) -> None:
        await self.close(discord_id, started_at)

        record = ListeningSession(
            discord_id=discord_id,
            started_at=started_at,
            track=spotify.title,
            track_id=spotify.track_id,
            track_url=spotify.track_url,
            artist=spotify.artist,
            album=spotify.album,
            album_cover_url=spotify.album_cover_url,
            duration=spotify.duration,
            party_id=spotify.party_id,
            declared_start=spotify.start,
            declared_end=spotify.end,
        )

        await self._add(record)

    async def pair_overlap(self, limit: int) -> list[PairOverlap]:
        first = aliased(ListeningSession)
        second = aliased(ListeningSession)

        duration = self._overlap_duration(first, second)

        query = (
            select(
                first.discord_id.label('source'),
                second.discord_id.label('target'),
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .select_from(first)
            .join(
                second,
                and_(
                    first.track_id == second.track_id,
                    first.discord_id < second.discord_id,
                    self._overlap_condition(first, second),
                ),
            )
            .where(first.track_id.isnot(None))
            .where(first.ended_at.isnot(None))
            .where(second.ended_at.isnot(None))
            .group_by(first.discord_id, second.discord_id)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)
        return self._pair_overlaps(rows)

    async def track_leaderboard(self, limit: int) -> list[TrackStat]:
        duration = func.sum(ListeningSession.ended_at - ListeningSession.started_at)

        query = (
            select(
                ListeningSession.track,
                ListeningSession.artist,
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .where(ListeningSession.ended_at.isnot(None))
            .group_by(ListeningSession.track, ListeningSession.artist)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)

        return [
            TrackStat(
                track=row.track,
                artist=row.artist,
                duration=row.duration,
                sessions=row.sessions,
            )
            for row in rows
        ]


class StatusSessionRepository(SessionRepository):
    model = StatusSession

    async def close(self, discord_id: int, ended_at: datetime) -> None:
        statement = (
            update(StatusSession)
            .where(StatusSession.discord_id == discord_id)
            .where(StatusSession.ended_at.is_(None))
            .values(ended_at=ended_at)
        )

        await self._execute(statement)

    async def member_devices(self, discord_id: int) -> DeviceStat:
        duration = StatusSession.ended_at - StatusSession.started_at

        query = (
            select(
                func.sum(duration).filter(StatusSession.desktop.is_(True)).label('desktop'),
                func.sum(duration).filter(StatusSession.web.is_(True)).label('web'),
                func.sum(duration).filter(StatusSession.mobile.is_(True)).label('mobile'),
            )
            .where(StatusSession.discord_id == discord_id)
            .where(StatusSession.ended_at.isnot(None))
        )

        row = await self._first(query)

        if row is None:
            return DeviceStat(desktop=None, web=None, mobile=None)

        return DeviceStat(desktop=row.desktop, web=row.web, mobile=row.mobile)

    async def member_last(self, discord_id: int) -> LastStatus | None:
        query = (
            select(
                StatusSession.status,
                StatusSession.started_at,
                StatusSession.ended_at,
            )
            .where(StatusSession.discord_id == discord_id)
            .order_by(StatusSession.started_at.desc())
            .limit(1)
        )

        row = await self._first(query)

        if row is None:
            return None

        return LastStatus(
            status=row.status,
            started_at=row.started_at,
            ended_at=row.ended_at,
        )

    async def member_total(self, discord_id: int) -> timedelta | None:
        duration = func.sum(StatusSession.ended_at - StatusSession.started_at)

        query = (
            select(duration)
            .where(StatusSession.discord_id == discord_id)
            .where(StatusSession.ended_at.isnot(None))
        )

        return await self._scalar(query)

    async def online_leaderboard(self, limit: int) -> list[MemberStat]:
        duration = func.sum(StatusSession.ended_at - StatusSession.started_at)

        query = (
            select(
                StatusSession.discord_id,
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .where(StatusSession.ended_at.isnot(None))
            .group_by(StatusSession.discord_id)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)

        return [
            MemberStat(discord_id=row.discord_id, duration=row.duration, sessions=row.sessions)
            for row in rows
        ]

    async def open(self, member: discord.Member, started_at: datetime) -> None:
        await self.close(member.id, started_at)

        offline = discord.Status.offline

        record = StatusSession(
            discord_id=member.id,
            started_at=started_at,
            status=member.status.value,
            desktop=member.desktop_status is not offline,
            web=member.web_status is not offline,
            mobile=member.mobile_status is not offline,
        )

        await self._add(record)


class VoiceSessionRepository(SessionRepository):
    model = VoiceSession

    @staticmethod
    def _state(state: discord.VoiceState) -> dict[str, Any]:
        return {
            'streaming': state.self_stream,
            'video': state.self_video,
            'self_mute': state.self_mute,
            'self_deaf': state.self_deaf,
            'server_mute': state.mute,
            'server_deaf': state.deaf,
            'suppress': state.suppress,
            'afk': state.afk,
        }

    async def channel_leaderboard(self, limit: int) -> list[ChannelStat]:
        duration = func.sum(VoiceSession.ended_at - VoiceSession.started_at)

        query = (
            select(
                VoiceSession.channel_id,
                func.max(VoiceSession.channel_name).label('channel_name'),
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .where(VoiceSession.ended_at.isnot(None))
            .group_by(VoiceSession.channel_id)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)

        return [
            ChannelStat(
                channel_id=row.channel_id,
                channel_name=row.channel_name,
                duration=row.duration,
                sessions=row.sessions,
            )
            for row in rows
        ]

    async def close(self, discord_id: int, ended_at: datetime) -> None:
        statement = (
            update(VoiceSession)
            .where(VoiceSession.discord_id == discord_id)
            .where(VoiceSession.ended_at.is_(None))
            .values(ended_at=ended_at)
        )

        await self._execute(statement)

    async def member_duo(self, discord_id: int, limit: int) -> list[MemberStat]:
        first = aliased(VoiceSession)
        second = aliased(VoiceSession)

        duration = self._overlap_duration(first, second)

        query = (
            select(
                second.discord_id,
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .select_from(first)
            .join(
                second,
                and_(
                    first.channel_id == second.channel_id,
                    first.discord_id != second.discord_id,
                    self._overlap_condition(first, second),
                ),
            )
            .where(first.discord_id == discord_id)
            .where(first.ended_at.isnot(None))
            .where(second.ended_at.isnot(None))
            .group_by(second.discord_id)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)

        return [
            MemberStat(discord_id=row.discord_id, duration=row.duration, sessions=row.sessions)
            for row in rows
        ]

    async def member_last(self, discord_id: int) -> LastVoice | None:
        query = (
            select(
                VoiceSession.channel_name,
                VoiceSession.started_at,
                VoiceSession.ended_at,
            )
            .where(VoiceSession.discord_id == discord_id)
            .order_by(VoiceSession.started_at.desc())
            .limit(1)
        )

        row = await self._first(query)

        if row is None:
            return None

        return LastVoice(
            channel_name=row.channel_name,
            started_at=row.started_at,
            ended_at=row.ended_at,
        )

    async def member_total(self, discord_id: int) -> timedelta | None:
        duration = func.sum(VoiceSession.ended_at - VoiceSession.started_at)

        query = (
            select(duration)
            .where(VoiceSession.discord_id == discord_id)
            .where(VoiceSession.ended_at.isnot(None))
        )

        return await self._scalar(query)

    async def member_voice(self, discord_id: int, limit: int) -> list[ChannelStat]:
        duration = func.sum(VoiceSession.ended_at - VoiceSession.started_at)

        query = (
            select(
                VoiceSession.channel_id,
                func.max(VoiceSession.channel_name).label('channel_name'),
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .where(VoiceSession.discord_id == discord_id)
            .where(VoiceSession.ended_at.isnot(None))
            .group_by(VoiceSession.channel_id)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)

        return [
            ChannelStat(
                channel_id=row.channel_id,
                channel_name=row.channel_name,
                duration=row.duration,
                sessions=row.sessions,
            )
            for row in rows
        ]

    async def open(
        self,
        member: discord.Member,
        state: discord.VoiceState,
        started_at: datetime
    ) -> None:
        await self.close(member.id, started_at)

        channel = state.channel

        async with self._session_maker() as session:
            record = VoiceSession(
                discord_id=member.id,
                started_at=started_at,
                channel_id=channel.id,
                channel_name=channel.name,
                session_id=state.session_id,
            )

            session.add(record)
            await session.flush()

            child = VoiceState(
                session_id=record.id,
                changed_at=started_at,
                **self._state(state),
            )

            session.add(child)

            await session.commit()

    async def pair_overlap(self, limit: int) -> list[PairOverlap]:
        first = aliased(VoiceSession)
        second = aliased(VoiceSession)

        duration = self._overlap_duration(first, second)

        query = (
            select(
                first.discord_id.label('source'),
                second.discord_id.label('target'),
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .select_from(first)
            .join(
                second,
                and_(
                    first.channel_id == second.channel_id,
                    first.discord_id < second.discord_id,
                    self._overlap_condition(first, second),
                ),
            )
            .where(first.ended_at.isnot(None))
            .where(second.ended_at.isnot(None))
            .group_by(first.discord_id, second.discord_id)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)
        return self._pair_overlaps(rows)

    async def state_sync(
        self,
        discord_id: int,
        state: discord.VoiceState,
        moment: datetime
    ) -> None:
        conditions = [
            VoiceSession.discord_id == discord_id,
            VoiceSession.ended_at.is_(None),
        ]

        values = self._state(state)

        async with self._session_maker() as session:
            open_id = await session.scalar(
                select(VoiceSession.id).where(*conditions)
            )

            if open_id is None:
                return

            latest = await session.scalar(
                select(VoiceState)
                .where(VoiceState.session_id == open_id)
                .order_by(VoiceState.changed_at.desc())
                .limit(1)
            )

            if latest is not None:
                current = {key: getattr(latest, key) for key in values}

                if current == values:
                    return

            child = VoiceState(session_id=open_id, changed_at=moment, **values)
            session.add(child)

            await session.commit()

    async def streamer_leaderboard(self, limit: int) -> list[MemberStat]:
        following = func.lead(VoiceState.changed_at).over(
            partition_by=VoiceState.session_id,
            order_by=VoiceState.changed_at,
        )

        boundary = func.coalesce(following, VoiceSession.ended_at)

        intervals = (
            select(
                VoiceSession.discord_id.label('discord_id'),
                VoiceState.session_id.label('session_id'),
                VoiceState.streaming.label('streaming'),
                VoiceState.changed_at.label('started_at'),
                func.greatest(boundary, VoiceState.changed_at).label('ended_at'),
            )
            .select_from(VoiceSession)
            .join(VoiceState, VoiceState.session_id == VoiceSession.id)
            .where(VoiceSession.ended_at.isnot(None))
            .subquery()
        )

        duration = func.sum(intervals.c.ended_at - intervals.c.started_at)

        query = (
            select(
                intervals.c.discord_id,
                duration.label('duration'),
                func.count(distinct(intervals.c.session_id)).label('sessions'),
            )
            .where(intervals.c.streaming.is_(True))
            .group_by(intervals.c.discord_id)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)

        return [
            MemberStat(discord_id=row.discord_id, duration=row.duration, sessions=row.sessions)
            for row in rows
        ]

    async def voice_leaderboard(self, limit: int) -> list[MemberStat]:
        duration = func.sum(VoiceSession.ended_at - VoiceSession.started_at)

        query = (
            select(
                VoiceSession.discord_id,
                duration.label('duration'),
                func.count().label('sessions'),
            )
            .where(VoiceSession.ended_at.isnot(None))
            .group_by(VoiceSession.discord_id)
            .order_by(duration.desc())
            .limit(limit)
        )

        rows = await self._all(query)

        return [
            MemberStat(discord_id=row.discord_id, duration=row.duration, sessions=row.sessions)
            for row in rows
        ]
