from __future__ import annotations

import msgspec

from datetime import datetime

from core.time import date_format


class DiscordRoleError(Exception):
    """
    A DiscordRoleError is raised when a role is not found in the database
    from user input. This can include by an ID or name.
    """


class DiscordRole(msgspec.Struct):
    identifier: int | None = None
    name: str | None = None
    colour: str | None = None
    hoist: bool | None = None
    position: int | None = None
    managed: bool | None = None
    mentionable: bool | None = None
    is_default: bool | None = None
    created_at: datetime | None = None

    @property
    def created(self) -> str:
        return date_format(self.created_at)
