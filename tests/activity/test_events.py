from __future__ import annotations

import discord
import pytest

from activity.events import PresenceSnapshot, VoiceSnapshot


VOICE_STATE = {
    'deaf': False,
    'mute': False,
    'self_deaf': False,
    'self_mute': False,
    'self_stream': False,
    'self_video': False,
    'session_id': 'session',
    'suppress': False,
}


class ChannelStub:
    def __init__(self, identifier: int, name: str) -> None:
        self.id = identifier
        self.name = name


class MemberStub:
    def __init__(
        self,
        identifier: int = 124459096819630080,
        *,
        status: discord.Status = discord.Status.online,
        desktop: discord.Status = discord.Status.online,
        web: discord.Status = discord.Status.offline,
        mobile: discord.Status = discord.Status.offline,
        activities: tuple[discord.BaseActivity, ...] = ()
    ) -> None:
        self.id = identifier
        self.status = status
        self.desktop_status = desktop
        self.web_status = web
        self.mobile_status = mobile
        self.activities = activities


def voice_build(channel: ChannelStub | None = None, **override: bool) -> VoiceSnapshot:
    state = discord.VoiceState(data={**VOICE_STATE, **override}, channel=channel)

    return VoiceSnapshot.capture(MemberStub(), state)


def test_presence_capture_is_detached_from_the_member() -> None:
    member = MemberStub(activities=(discord.Game('Elden Ring'),))

    snapshot = PresenceSnapshot.capture(member)
    member.activities = (discord.Game('Balatro'),)

    assert [activity.name for activity in snapshot.activities] == ['Elden Ring']


def test_presence_capture_flattens_devices() -> None:
    member = MemberStub(mobile=discord.Status.idle)

    snapshot = PresenceSnapshot.capture(member)

    assert snapshot.discord_id == 124459096819630080
    assert snapshot.desktop
    assert snapshot.mobile
    assert not snapshot.web


def test_presence_key_matches_identical_presence() -> None:
    first = PresenceSnapshot.capture(MemberStub())
    second = PresenceSnapshot.capture(MemberStub())

    assert first.key == second.key


def test_presence_key_detects_change() -> None:
    first = PresenceSnapshot.capture(MemberStub())
    second = PresenceSnapshot.capture(MemberStub(status=discord.Status.idle))

    assert first.key != second.key


@pytest.mark.parametrize(
    ('status', 'expected'),
    [
        (discord.Status.online, True),
        (discord.Status.idle, True),
        (discord.Status.dnd, True),
        (discord.Status.offline, False),
    ]
)
def test_presence_online(status: discord.Status, expected: bool) -> None:
    snapshot = PresenceSnapshot.capture(MemberStub(status=status))

    assert snapshot.online == expected


def test_voice_capture_without_channel() -> None:
    snapshot = voice_build()

    assert snapshot.channel_id is None
    assert snapshot.channel_name is None


def test_voice_capture_with_channel() -> None:
    channel = ChannelStub(863292513141522435, 'General')

    snapshot = voice_build(channel)

    assert snapshot.channel_id == 863292513141522435
    assert snapshot.channel_name == 'General'
    assert snapshot.session_id == 'session'


def test_voice_key_matches_identical_state() -> None:
    assert voice_build().key == voice_build().key


def test_voice_key_detects_change() -> None:
    assert voice_build().key != voice_build(self_mute=True).key


def test_voice_state_maps_to_columns() -> None:
    snapshot = voice_build(self_stream=True, mute=True)

    assert snapshot.state == {
        'streaming': True,
        'video': False,
        'self_mute': False,
        'self_deaf': False,
        'server_mute': True,
        'server_deaf': False,
        'suppress': False,
        'afk': False,
    }
