from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    Interval,
    SmallInteger,
    TEXT,
    VARCHAR,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column


class CommandMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    aliases: Mapped[list[str] | None] = mapped_column(ARRAY(TEXT), nullable=True)


class MemberMixin:
    __tablename__ = 'member'

    discord_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(TEXT, nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(TEXT, nullable=False)
    nickname: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    bot: Mapped[bool] = mapped_column(Boolean, nullable=False)
    previous_name: Mapped[list[str] | None] = mapped_column(ARRAY(TEXT), nullable=True)
    previous_nickname: Mapped[list[str] | None] = mapped_column(ARRAY(TEXT), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    banned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RoleMixin:
    __tablename__ = 'role'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    colour: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    hoist: Mapped[bool] = mapped_column(Boolean, nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    managed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    mentionable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SoundMixin:
    __tablename__ = 'sound'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(TEXT), nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SessionMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StateMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ActivitySessionMixin(SessionMixin):
    __tablename__ = 'activity_session'

    type: Mapped[str] = mapped_column(VARCHAR(16), nullable=False)
    name: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    application_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    url: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    platform: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    declared_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    declared_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ActivityStateMixin(StateMixin):
    __tablename__ = 'activity_state'

    details: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    state: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    emoji: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    party_size: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    party_max: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    large_text: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    small_text: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    large_image: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    small_image: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    buttons: Mapped[list[str] | None] = mapped_column(ARRAY(TEXT), nullable=True)


class ListeningSessionMixin(SessionMixin):
    __tablename__ = 'listening_session'

    track: Mapped[str] = mapped_column(TEXT, nullable=False)
    track_id: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    track_url: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    artist: Mapped[str] = mapped_column(TEXT, nullable=False)
    album: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    album_cover_url: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    duration: Mapped[timedelta | None] = mapped_column(Interval, nullable=True)
    party_id: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    declared_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    declared_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StatusSessionMixin(SessionMixin):
    __tablename__ = 'status_session'

    status: Mapped[str] = mapped_column(VARCHAR(8), nullable=False)
    desktop: Mapped[bool] = mapped_column(Boolean, nullable=False)
    web: Mapped[bool] = mapped_column(Boolean, nullable=False)
    mobile: Mapped[bool] = mapped_column(Boolean, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VoiceSessionMixin(SessionMixin):
    __tablename__ = 'voice_session'

    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel_name: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    session_id: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)


class VoiceStateMixin(StateMixin):
    __tablename__ = 'voice_state'

    streaming: Mapped[bool] = mapped_column(Boolean, nullable=False)
    video: Mapped[bool] = mapped_column(Boolean, nullable=False)
    self_mute: Mapped[bool] = mapped_column(Boolean, nullable=False)
    self_deaf: Mapped[bool] = mapped_column(Boolean, nullable=False)
    server_mute: Mapped[bool] = mapped_column(Boolean, nullable=False)
    server_deaf: Mapped[bool] = mapped_column(Boolean, nullable=False)
    suppress: Mapped[bool] = mapped_column(Boolean, nullable=False)
    afk: Mapped[bool] = mapped_column(Boolean, nullable=False)
