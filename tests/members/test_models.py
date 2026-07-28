from __future__ import annotations

import pytest

from datetime import datetime, UTC

from members.models import DiscordMember, DiscordMemberError


@pytest.fixture
def member() -> DiscordMember:
    return DiscordMember(
        identifier=863292513141522433,
        name='braycarlson',
        display_name='Brayden',
        nickname='Brayden',
        role_identifier=863292513141522434,
        bot=False,
        created_at=datetime(2015, 3, 14, tzinfo=UTC),
        joined_at=datetime(2021, 7, 10, tzinfo=UTC),
        updated_at=datetime(2026, 7, 27, tzinfo=UTC),
    )


def test_discord_member_error_is_exception() -> None:
    assert issubclass(DiscordMemberError, Exception)


def test_discord_member_created(member: DiscordMember) -> None:
    assert member.created == 'March 14, 2015'


def test_discord_member_joined(member: DiscordMember) -> None:
    assert member.joined == 'July 10, 2021'


def test_discord_member_updated(member: DiscordMember) -> None:
    assert member.updated == 'July 27, 2026'


def test_discord_member_defaults() -> None:
    member = DiscordMember()

    assert member.created == 'Unknown'
    assert member.joined == 'Unknown'
    assert member.updated == 'Unknown'


def test_discord_member_is_not_banned_or_removed(member: DiscordMember) -> None:
    assert member.banned_at is None
    assert member.removed_at is None
