from __future__ import annotations

import asyncio

from asyncio import timeout
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from typing_extensions import Any

    from discord import Guild
    from discord.ext.commands import Context


QUEUE_IDLE_TIMEOUT_SECONDS = 30


class Player:
    def __init__(self, ctx: Context) -> None:
        self._callbacks: set[asyncio.Task[None]] = set()

        self.cog = ctx.cog
        self.guild = ctx.guild
        self.viking = ctx.bot

        self.event = asyncio.Event()
        self.queue = asyncio.Queue()
        self.task: asyncio.Task[None] | None = None

    def _after_callback_create(
        self,
        callback: Callable[[], Coroutine[Any, Any, None]] | None
    ) -> Callable[[Exception | None], None]:
        def after(_: Exception | None) -> None:
            self.viking.loop.call_soon_threadsafe(self.event.set)

            if callback is not None:
                self.viking.loop.call_soon_threadsafe(
                    lambda callback=callback: self._callback_schedule(callback)
                )

        return after

    def _callback_schedule(
        self,
        callback: Callable[[], Coroutine[Any, Any, None]]
    ) -> None:
        task = self.viking.loop.create_task(callback())

        self._callbacks.add(task)
        task.add_done_callback(self._callbacks.discard)

    def cancel(self) -> None:
        current = asyncio.current_task()

        for task in list(self._callbacks):
            if task is not current:
                task.cancel()

        self._callbacks.clear()

        task = self.task
        self.task = None

        if task is None:
            return

        if task is not current:
            task.cancel()

    async def destroy(self, guild: Guild) -> None:
        await self.cog.cleanup(guild)

    async def player_loop(self) -> None:
        await self.viking.wait_until_ready()

        source = None

        while not self.viking.is_closed():
            self.event.clear()

            try:
                async with timeout(QUEUE_IDLE_TIMEOUT_SECONDS):
                    source, callback = await self.queue.get()
            except TimeoutError:
                await self.destroy(self.guild)
                return

            after = self._after_callback_create(callback)
            self.guild.voice_client.play(source, after=after)

            await self.event.wait()

        if source is not None:
            source.cleanup()

    def start(self) -> None:
        if self.task is not None:
            return

        self.task = self.viking.loop.create_task(self.player_loop())
