from __future__ import annotations

import asyncio
import discord

from model.member import DiscordMember, DiscordMemberError
from sqlalchemy import func
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord.ext.commands import Context
    from sqlalchemy.engine.result import RowProxy


class MemberInterface:
    def __init__(self, ctx: Context, identifier: str):
        self.ctx = ctx
        self.identifier = identifier
        self.viking = self.ctx.bot

    async def get(self) -> str | None:
        discord_id = None

        try:
            discord_id = await self.from_id()
        except DiscordMemberError:
            message = 'No member found.'
            await self.ctx.send(message)
        except asyncio.TimeoutError:
            message = 'You have run out of time. Please try again.'
            await self.ctx.send(message)

        return discord_id

    async def from_id(self) -> str:
        """
        A function to get a member by ID from the database.
        """

        try:
            discord_id = int(self.identifier)
        except ValueError:
            name = self.identifier.lower()
            return await self.from_name(name)
        else:
            row = (
                await self.viking.guild.member
                .select('discord_id')
                .where(self.viking.guild.member.discord_id == discord_id)
                .gino
                .scalar()
            )

            if row is None:
                raise DiscordMemberError

            return row

    async def from_name(self, name: str) -> None:
        """
        A function to get a member by account name or nickname from the
        database.
        """

        model = self.viking.guild.member

        condition = (
            (func.levenshtein(func.lower(model.display_name), name) <= 3) |
            (func.levenshtein(func.lower(model.name), name) <= 3) |
            (func.levenshtein(func.lower(model.nickname), name) <= 3)
        )

        rows = (
            await model
            .select(
                'discord_id',
                'display_name',
                'name',
                'nickname'
            )
            .where(condition)
            .limit(5)
            .gino
            .all()
        )

        length = len(rows)

        match length:
            case 0:
                raise DiscordMemberError

            case 1:
                row, *_ = rows
                return dict(row).get('discord_id')

            case _:
                target = []

                for row in rows:
                    display_name = dict(row).get('display_name').lower()

                    if name == display_name.lower():
                        target.append(row)

                if len(target) == 1:
                    for member in target:
                        return dict(member).get('discord_id')

                await self.display_identical(rows)

                indices = {
                    index: dict(row).get('discord_id')
                    for index, row in enumerate(rows, 1)
                }

                return await self.from_index(indices)

    async def from_index(self, indices: list[int]) -> str:
        def check(message: str) -> bool:
            condition = (
                message.author == self.ctx.author and
                message.channel == self.ctx.channel
            )

            if condition:
                return True

            return False

        try:
            message = await self.viking.wait_for(
                'message',
                check=check,
                timeout=15
            )
        except asyncio.TimeoutError:
            raise
        else:
            try:
                index = int(message.content)

                if index in indices:
                    index = int(message.content)
                    return indices[index]
            except Exception as exception:
                raise DiscordMemberError

    async def display_identical(self, rows: list[RowProxy]) -> None:
        """
        A function that will output each member with an identical account
        name or nickname.
        """

        length = len(rows)

        color = discord.Colour.purple()
        title = f"There are {length} members with identical information."

        embed = discord.Embed(color=color, title=title)

        for index, row in enumerate(rows, 1):
            row = dict(row)
            member = DiscordMember(row)

            embed.add_field(name='#', value=index)
            embed.add_field(name='Name', value=member.name)
            embed.add_field(name='Nickname', value=member.display_name)

        await self.ctx.send(embed=embed)
