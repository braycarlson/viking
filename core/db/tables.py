from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from core.db.engine import CommandBase, GuildBase
from core.db.schema import (
    ActivitySessionMixin,
    ActivityStateMixin,
    CommandMixin,
    ListeningSessionMixin,
    MemberMixin,
    RoleMixin,
    SoundMixin,
    StatusSessionMixin,
    VoiceSessionMixin,
    VoiceStateMixin,
)


class Hidden(CommandMixin, CommandBase):
    __tablename__ = 'hidden'

    __table_args__ = (
        Index('index_hidden_name', 'name', unique=True),
    )


class Public(CommandMixin, CommandBase):
    __tablename__ = 'public'

    __table_args__ = (
        Index('index_public_name', 'name', unique=True),
    )


class Member(MemberMixin, GuildBase):
    __tablename__ = 'member'

    role_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('role.id'), nullable=True)

    __table_args__ = (
        Index('index_member_name', text('lower(name)')),
        Index('index_member_nickname', text('lower(nickname)')),
    )


class Role(RoleMixin, GuildBase):
    __tablename__ = 'role'

    __table_args__ = (
        Index('index_role_id', 'id', unique=True),
        Index('index_role_name', text('lower(name)')),
    )


class Sound(SoundMixin, GuildBase):
    __tablename__ = 'sound'

    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('member.discord_id'), nullable=False
    )

    __table_args__ = (
        Index('index_sound_name', text('lower(name)')),
    )


class ActivitySession(ActivitySessionMixin, GuildBase):
    __tablename__ = 'activity_session'

    __table_args__ = (
        Index(
            'index_activity_session_open',
            'discord_id',
            'type',
            'name',
            unique=True,
            postgresql_where=text('ended_at IS NULL'),
        ),
        Index('index_activity_session_member', 'discord_id'),
        Index('index_activity_session_name', text('lower(name)')),
        Index('index_activity_session_started', 'started_at'),
        Index(
            'index_activity_session_period',
            text('tstzrange(started_at, ended_at)'),
            postgresql_using='gist',
        ),
    )


class ActivityState(ActivityStateMixin, GuildBase):
    __tablename__ = 'activity_state'

    session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('activity_session.id', ondelete='CASCADE'),
        nullable=False,
    )

    __table_args__ = (
        Index('index_activity_state_session', 'session_id', 'changed_at'),
    )


class ListeningSession(ListeningSessionMixin, GuildBase):
    __tablename__ = 'listening_session'

    __table_args__ = (
        Index(
            'index_listening_session_open',
            'discord_id',
            unique=True,
            postgresql_where=text('ended_at IS NULL'),
        ),
        Index('index_listening_session_member', 'discord_id'),
        Index('index_listening_session_artist', text('lower(artist)')),
        Index('index_listening_session_track', text('lower(track)')),
        Index('index_listening_session_started', 'started_at'),
    )


class StatusSession(StatusSessionMixin, GuildBase):
    __tablename__ = 'status_session'

    __table_args__ = (
        Index(
            'index_status_session_open',
            'discord_id',
            unique=True,
            postgresql_where=text('ended_at IS NULL'),
        ),
        Index('index_status_session_member', 'discord_id'),
        Index('index_status_session_started', 'started_at'),
    )


class VoiceSession(VoiceSessionMixin, GuildBase):
    __tablename__ = 'voice_session'

    __table_args__ = (
        Index(
            'index_voice_session_open',
            'discord_id',
            unique=True,
            postgresql_where=text('ended_at IS NULL'),
        ),
        Index('index_voice_session_member', 'discord_id'),
        Index('index_voice_session_channel', 'channel_id'),
        Index('index_voice_session_started', 'started_at'),
        Index(
            'index_voice_session_period',
            text('tstzrange(started_at, ended_at)'),
            postgresql_using='gist',
        ),
    )


class VoiceState(VoiceStateMixin, GuildBase):
    __tablename__ = 'voice_state'

    session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('voice_session.id', ondelete='CASCADE'),
        nullable=False,
    )

    __table_args__ = (
        Index('index_voice_state_session', 'session_id', 'changed_at'),
    )
