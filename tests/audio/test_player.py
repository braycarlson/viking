from __future__ import annotations

import asyncio

import pytest

from typing_extensions import TYPE_CHECKING

from audio.cog import Audio
from audio.player import Player

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from typing_extensions import Any


pytestmark = pytest.mark.asyncio

GUILD_IDENTIFIER = 863292513141522433


class BotStub:
    def __init__(self) -> None:
        self.closed = False
        self.loop = asyncio.get_event_loop()

    def is_closed(self) -> bool:
        return self.closed

    async def wait_until_ready(self) -> None:
        return


class GuildStub:
    def __init__(self, identifier: int) -> None:
        self.id = identifier
        self.voice_client = None


class CogStub:
    def __init__(self) -> None:
        self.cleaned = []

    async def cleanup(self, guild: GuildStub) -> None:
        self.cleaned.append(guild)


class ContextStub:
    def __init__(self, identifier: int) -> None:
        self.bot = BotStub()
        self.cog = CogStub()
        self.guild = GuildStub(identifier)


def player_build(identifier: int = GUILD_IDENTIFIER) -> Player:
    ctx = ContextStub(identifier)
    return Player(ctx)


def audio_build(players: dict[int, Player]) -> Audio:
    audio = Audio.__new__(Audio)
    audio.players = players
    audio.views = {}

    return audio


async def blocking() -> None:
    await asyncio.Event().wait()


async def test_start_retains_the_loop_task() -> None:
    player = player_build()
    player.start()

    assert isinstance(player.task, asyncio.Task)

    player.cancel()


async def test_start_is_idempotent() -> None:
    player = player_build()
    player.start()

    task = player.task
    player.start()

    assert player.task is task

    player.cancel()


async def test_cancel_stops_the_loop_task() -> None:
    player = player_build()
    player.start()

    task = player.task
    player.cancel()

    assert player.task is None

    with pytest.raises(asyncio.CancelledError):
        await task

    assert task.cancelled()


async def test_cancel_without_a_task_is_a_noop() -> None:
    player = player_build()
    player.cancel()

    assert player.task is None


async def test_cancel_does_not_cancel_the_calling_task() -> None:
    player = player_build()
    player.task = asyncio.current_task()

    player.cancel()

    await asyncio.sleep(0)

    assert player.task is None
    assert not asyncio.current_task().cancelled()


async def test_callback_schedule_retains_the_task() -> None:
    player = player_build()
    player._callback_schedule(blocking)

    assert len(player._callbacks) == 1

    player.cancel()


async def test_callback_task_is_discarded_when_it_finishes() -> None:
    player = player_build()

    async def immediate() -> None:
        return

    player._callback_schedule(immediate)

    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert player._callbacks == set()


async def test_cancel_stops_pending_callbacks() -> None:
    player = player_build()
    player._callback_schedule(blocking)

    task, *_ = player._callbacks
    player.cancel()

    assert player._callbacks == set()

    with pytest.raises(asyncio.CancelledError):
        await task


async def test_destroy_delegates_to_the_cog() -> None:
    player = player_build()
    await player.destroy(player.guild)

    assert player.cog.cleaned == [player.guild]


async def test_cleanup_cancels_and_drops_the_player() -> None:
    player = player_build()
    player.start()

    task = player.task
    audio = audio_build({GUILD_IDENTIFIER: player})

    await audio.cleanup(player.guild)

    assert audio.players == {}
    assert player.task is None

    with pytest.raises(asyncio.CancelledError):
        await task


async def test_cleanup_without_a_player_is_a_noop() -> None:
    audio = audio_build({})
    guild = GuildStub(GUILD_IDENTIFIER)

    await audio.cleanup(guild)

    assert audio.players == {}


async def test_cog_unload_cancels_every_player() -> None:
    first = player_build(1)
    second = player_build(2)

    first.start()
    second.start()

    tasks = [first.task, second.task]
    audio = audio_build({1: first, 2: second})

    await audio.cog_unload()

    assert audio.players == {}
    assert audio.views == {}

    for task in tasks:
        with pytest.raises(asyncio.CancelledError):
            await task


async def test_player_loop_destroys_itself_when_idle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr('audio.player.QUEUE_IDLE_TIMEOUT_SECONDS', 0.01)

    player = player_build()
    await player.player_loop()

    assert player.cog.cleaned == [player.guild]


async def test_player_loop_survives_cleanup_cancelling_it() -> None:
    player = player_build()
    audio = audio_build({GUILD_IDENTIFIER: player})

    async def cleanup(guild: GuildStub) -> None:
        await audio.cleanup(guild)

    player.cog.cleanup = cleanup
    player.task = asyncio.current_task()

    await player.destroy(player.guild)

    assert audio.players == {}
    assert player.task is None
    assert not asyncio.current_task().cancelled()


async def test_after_callback_schedules_through_the_player(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    player = player_build()
    scheduled = []

    def schedule(callback: Coroutine[Any, Any, None]) -> None:
        scheduled.append(callback)

    monkeypatch.setattr(player, '_callback_schedule', schedule)

    after = player._after_callback_create(blocking)
    after(None)

    await asyncio.sleep(0)

    assert player.event.is_set()
    assert scheduled == [blocking]
