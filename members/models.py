from __future__ import annotations

import msgspec

from datetime import datetime

from core.time import date_format


class DiscordMemberError(Exception):
    """
    A DiscordMemberError is raised when a member is not found in the
    database from user input. This can include by an ID, account name
    or nickname.
    """


class DiscordMember(msgspec.Struct):
    identifier: int | None = None
    name: str | None = None
    display_name: str | None = None
    nickname: str | None = None
    role_identifier: int | None = None
    bot: bool | None = None
    previous_name: list[str] | None = None
    previous_nickname: list[str] | None = None
    created_at: datetime | None = None
    joined_at: datetime | None = None
    updated_at: datetime | None = None
    removed_at: datetime | None = None
    banned_at: datetime | None = None

    @property
    def created(self) -> str:
        return date_format(self.created_at)

    @property
    def joined(self) -> str:
        return date_format(self.joined_at)

    @property
    def updated(self) -> str:
        return date_format(self.updated_at)
