from __future__ import annotations

import logging

from discord.ext import commands
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Viking
    from discord.ext.commands import Context


log = logging.getLogger(__name__)


class Discord(commands.Cog):
    def __init__(self, viking: Viking):
        self.viking = viking

    @commands.command()
    async def invite(self, ctx: Context) -> None:
        """
        *invite

        A command that generates an invite to the guild.
        """

        await ctx.message.delete()
        await ctx.send(await ctx.message.channel.create_invite())

    @commands.command()
    async def members(self, ctx: Context) -> None:
        """
        *members

        A command that displays the total number of Discord members in
        the guild.
        """

        count = (
            await
            self.viking.guild.engine
            .func
            .count(self.viking.guild.member.discord_id)
            .gino
            .scalar()
        )

        await ctx.send(f"There are {count} members in this server")

    @commands.command()
    async def nicknames(self, ctx: Context) -> None:
        """
        *nicknames

        A command that displays the total number of Discord members
        with nicknames in the guild.
        """

        count = (
            await
            self.viking.guild.engine
            .func
            .count(self.viking.guild.member.nickname)
            .gino
            .scalar()
        )

        await ctx.send(f"There are {count} members with nicknames")

    @commands.command()
    async def owner(self, ctx: Context) -> None:
        """
        *owner

        A command that mentions the owner of the Discord server.
        """

        await ctx.send(ctx.guild.owner.mention)

    @commands.command()
    @commands.cooldown(rate=1, per=30.0, type=commands.BucketType.default)
    async def ping(self, ctx: Context) -> None:
        """
        *ping

        A command that displays the latency to the Discord server.
        """

        await ctx.send(f"Ping: {self.viking.latency * 1000:.0f} ms")


async def setup(viking: Viking) -> None:
    discord = Discord(viking)
    await viking.add_cog(discord)
