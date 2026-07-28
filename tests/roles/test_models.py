from __future__ import annotations

import pytest

from datetime import datetime, UTC

from roles.models import DiscordRole, DiscordRoleError


@pytest.fixture
def role() -> DiscordRole:
    return DiscordRole(
        identifier=863292513141522434,
        name='Viking',
        colour='#9b59b6',
        hoist=True,
        position=3,
        managed=False,
        mentionable=False,
        is_default=False,
        created_at=datetime(2021, 7, 10, tzinfo=UTC),
    )


def test_discord_role_error_is_exception() -> None:
    assert issubclass(DiscordRoleError, Exception)


def test_discord_role_created(role: DiscordRole) -> None:
    assert role.created == 'July 10, 2021'


def test_discord_role_created_unknown() -> None:
    role = DiscordRole(name='Viking')
    assert role.created == 'Unknown'
