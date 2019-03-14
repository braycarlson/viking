import discord
import logging
from discord.ext import commands


log = logging.getLogger(__name__)


class Discord:
    def __init__(self, viking):
        self.viking = viking
        self.color = viking.color

    @commands.command()
    async def invite(self, ctx):
        """*invite

        A command that generates an invite link to the server.
        """

        await ctx.send(await ctx.message.channel.create_invite())

    @commands.command()
    async def joined(self, ctx, *, member: discord.Member):
        """*joined <member>

        A command that will return the date of when a specified Discord member
        joined the server.
        """

        date = member.joined_at.strftime('%B %d, %Y')
        await ctx.send(f"{member.name} joined this server on {date}")

    @commands.command()
    async def members(self, ctx):
        """*members

        A command that will return the total number of Discord members
        in the server.
        """

        await ctx.send(f"There are `{ctx.guild.member_count}` members in this server.")

    @commands.command()
    async def owner(self, ctx):
        """*owner

        A command that will mention the owner of the Discord server.
        """

        await ctx.send(ctx.guild.owner.mention)

    @commands.command()
    @commands.cooldown(rate=1, per=30.0, type=commands.BucketType.default)
    async def ping(self, ctx):
        """*ping

        A command that will tell you the bot's latency.
        """

        await ctx.send(f"**Ping:** {self.viking.latency * 1000:.0f} ms")


def setup(viking):
    viking.add_cog(Discord(viking))
