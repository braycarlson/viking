from __future__ import annotations

import asyncio

import discord
import pytest

from moderation.cog import Moderation
from moderation.events import PendingRevert


pytestmark = pytest.mark.asyncio

REVERT_SECONDS_LONG = 3600


class BotStub:
    def __init__(self) -> None:
        self.loop = asyncio.get_event_loop()


class MemberStub:
    def __init__(self) -> None:
        self.reverted = 0

    def __str__(self) -> str:
        return 'member'


class ResponseStub:
    def __init__(self) -> None:
        self.reason = 'Forbidden'
        self.status = 403


def moderation_build() -> Moderation:
    moderation = Moderation.__new__(Moderation)
    moderation.viking = BotStub()
    moderation.reverts = set()
    moderation.unloading = asyncio.Event()

    return moderation


def pending_build(member: MemberStub) -> PendingRevert:
    async def revert(target: MemberStub) -> None:
        target.reverted = target.reverted + 1

    return PendingRevert(
        action='soft-mute',
        member=member,
        revert_function=revert
    )


def pending_failing_build(member: MemberStub) -> PendingRevert:
    async def revert(target: MemberStub) -> None:
        target.reverted = target.reverted + 1
        raise discord.HTTPException(ResponseStub(), 'missing permissions')

    return PendingRevert(
        action='soft-mute',
        member=member,
        revert_function=revert
    )


async def test_revert_schedule_retains_the_task() -> None:
    moderation = moderation_build()
    member = MemberStub()

    moderation._revert_schedule(pending_build(member), REVERT_SECONDS_LONG)

    assert len(moderation.reverts) == 1
    assert member.reverted == 0

    await moderation.cog_unload()


async def test_revert_runs_when_the_duration_elapses() -> None:
    moderation = moderation_build()
    member = MemberStub()

    moderation._revert_schedule(pending_build(member), 0)

    task, *_ = moderation.reverts
    await task

    assert member.reverted == 1


async def test_revert_task_is_discarded_when_it_finishes() -> None:
    moderation = moderation_build()
    member = MemberStub()

    moderation._revert_schedule(pending_build(member), 0)

    task, *_ = moderation.reverts
    await task

    await asyncio.sleep(0)

    assert moderation.reverts == set()


async def test_cog_unload_reverts_before_the_duration_elapses() -> None:
    moderation = moderation_build()
    member = MemberStub()

    moderation._revert_schedule(pending_build(member), REVERT_SECONDS_LONG)

    await moderation.cog_unload()

    assert member.reverted == 1
    assert moderation.unloading.is_set()


async def test_cog_unload_reverts_every_pending_action() -> None:
    moderation = moderation_build()
    members = [MemberStub(), MemberStub(), MemberStub()]

    for member in members:
        moderation._revert_schedule(pending_build(member), REVERT_SECONDS_LONG)

    await moderation.cog_unload()

    reverted = [member.reverted for member in members]
    assert reverted == [1, 1, 1]


async def test_cog_unload_without_pending_actions_is_a_noop() -> None:
    moderation = moderation_build()

    await moderation.cog_unload()

    assert moderation.reverts == set()


async def test_revert_survives_a_failing_revert_function() -> None:
    moderation = moderation_build()
    member = MemberStub()

    moderation._revert_schedule(pending_failing_build(member), 0)

    task, *_ = moderation.reverts
    await task

    assert member.reverted == 1
    assert task.exception() is None
