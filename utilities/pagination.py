from __future__ import annotations

import asyncio
import discord

from typing import TYPE_CHECKING
import contextlib

if TYPE_CHECKING:
    from discord import Embed, RawReactionActionEvent
    from discord.ext.commands import Context


class Pages:
    def __init__(
        self,
        ctx: Context, *,
        entries: list[str],
        per_page: int = 1
    ):
        self.bot = ctx.bot
        self.entries = entries
        self.message = ctx.message
        self.channel = ctx.channel
        self.author = ctx.author
        self.per_page = per_page

        pages, extra = divmod(len(self.entries), self.per_page)

        if extra:
            pages = pages + 1

        self.maximum_pages = pages
        self.embed = discord.Embed(colour=discord.Colour.purple())
        self.paginating = len(entries) > per_page

        self.reactions = [
            ('\N{BLACK LEFT-POINTING TRIANGLE}', self.previous_page),
            ('\N{BLACK SQUARE FOR STOP}', self.stop_pages),
            ('\N{BLACK RIGHT-POINTING TRIANGLE}', self.next_page),
        ]

    def get_page(self, page: int) -> list[str]:
        base = (page - 1) * self.per_page
        return self.entries[base:base + self.per_page]

    def get_content(
        self,
        entries: list[str],
        pages: int,
        *,
        first: bool = False
    ) -> None:
        return None

    def get_embed(self, entries: list[str], page: int, *, first: bool = False) -> Embed:
        self.prepare_embed(entries, page, first=first)
        return self.embed

    def prepare_embed(self, entries, page: int, *, first: bool = False):
        pass

    async def show_page(self, page: int, *, first: bool = False) -> None:
        self.current_page = page

        entries = self.get_page(page)
        content = self.get_content(entries, page, first=first)
        embed = self.get_embed(entries, page, first=first)

        if not self.paginating:
            return await self.channel.send(content=content, embed=embed)

        if not first:
            await self.message.edit(content=content, embed=embed)
            return None

        self.message = await self.channel.send(content=content, embed=embed)

        for (reaction, _) in self.reactions:
            await self.message.add_reaction(reaction)

        return None

    async def checked_show_page(self, page: int) -> None:
        if page != 0 and page <= self.maximum_pages:
            await self.show_page(page)

    async def next_page(self) -> None:
        await self.checked_show_page(self.current_page + 1)

    async def previous_page(self) -> None:
        await self.checked_show_page(self.current_page - 1)

    async def show_current_page(self) -> None:
        if self.paginating:
            await self.show_page(self.current_page)

    async def stop_pages(self) -> None:
        await self.message.delete()
        self.paginating = False

    def react_check(self, payload: RawReactionActionEvent) -> bool:
        if payload.user_id != self.author.id:
            return False

        if payload.message_id != self.message.id:
            return False

        to_check = str(payload.emoji)

        for (emoji, func) in self.reactions:
            if to_check == emoji:
                self.match = func
                return True

        return False

    async def paginate(self) -> None:
        first_page = self.show_page(1, first=True)

        if not self.paginating:
            await first_page
        else:
            self.bot.loop.create_task(first_page)

        while self.paginating:
            try:
                payload = await self.bot.wait_for(
                    'raw_reaction_add',
                    check=self.react_check,
                    timeout=120.0
                )
            except asyncio.TimeoutError:
                self.paginating = False

                try:
                    await self.message.clear_reactions()
                except Exception as exception:
                    pass
                finally:
                    break

            with contextlib.suppress(Exception):
                await self.message.remove_reaction(
                    payload.emoji,
                    discord.Object(id=payload.user_id)
                )

            await self.match()
