from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from discord.ext import commands

from members.repository import MemberRepository

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from bot import Viking


class Guild(commands.Cog):
    def __init__(self, viking: Viking) -> None:
        self.viking = viking

    @property
    def repository(self) -> MemberRepository:
        return MemberRepository(self.viking.guild.session)

    # Commands

    @commands.hybrid_command(description='Generate an invite to the guild.')
    async def invite(self, ctx: Context) -> None:
        """
        *invite

        A command that generates an invite to the guild.
        """

        await ctx.typing()

        if ctx.message is not None:
            await ctx.message.delete()

        invite = await ctx.channel.create_invite()
        await ctx.send(invite)

    @commands.hybrid_command(description='Display the total number of members in the guild.')
    async def members(self, ctx: Context) -> None:
        """
        *members

        A command that displays the total number of Discord members in
        the guild.
        """

        await ctx.typing()

        count = await self.repository.member_count()

        message = f'There are {count} members in this server.'
        await ctx.send(message)

    @commands.hybrid_command(description='Display the number of members with nicknames.')
    async def nicknames(self, ctx: Context) -> None:
        """
        *nicknames

        A command that displays the total number of Discord members
        with nicknames in the guild.
        """

        await ctx.typing()

        count = await self.repository.nickname_count()

        message = f'There are {count} members with nicknames.'
        await ctx.send(message)

    @commands.hybrid_command(description='Mention the owner of the server.')
    async def owner(self, ctx: Context) -> None:
        """
        *owner

        A command that mentions the owner of the Discord server.
        """

        message = ctx.guild.owner.mention
        await ctx.send(message)

    @commands.hybrid_command(description='Display the latency to the Discord server.')
    @commands.cooldown(rate=1, per=30.0, type=commands.BucketType.default)
    async def ping(self, ctx: Context) -> None:
        """
        *ping

        A command that displays the latency to the Discord server.
        """

        message = f'Ping: {self.viking.latency * 1000:.0f} ms'
        await ctx.send(message)


async def setup(viking: Viking) -> None:
    guild = Guild(viking)
    await viking.add_cog(guild)
