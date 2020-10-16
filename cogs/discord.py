import discord
import logging
from database.model import database, ActiveMembers
from discord.ext import commands
from utilities.format import format_list


log = logging.getLogger(__name__)


class Discord(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.administrator = viking.administrator
        self.moderator = viking.moderator
        self.normal = viking.normal

    @commands.command(aliases=['admins'])
    async def administrators(self, ctx):
        """
        *administrators

        A command that displays the names of the administrators in the
        guild.
        """

        rows = (
            await ActiveMembers
            .select('display_name')
            .where(ActiveMembers.role_id == self.administrator)
            .gino
            .all()
        )

        names = [dict(row).get('display_name') for row in rows]

        name = format_list(
            names,
            symbol='bullet',
            sort=True
        )

        embed = discord.Embed(color=self.viking.color)
        embed.add_field(name='Administrators', value=name)
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        """
        *invite

        A command that generates an invite to the guild.
        """

        await ctx.message.delete()
        await ctx.send(await ctx.message.channel.create_invite())

    @commands.command()
    async def members(self, ctx):
        """
        *members

        A command that displays the total number of Discord members in
        the guild.
        """

        count = await database.func.count(ActiveMembers.discord_id).gino.scalar()
        await ctx.send(f"There are {count} members in this server")

    @commands.command(aliases=['mods'])
    async def moderators(self, ctx):
        """
        *moderators

        A command that displays the names of the moderators in the guild.
        """

        rows = (
            await ActiveMembers
            .select('display_name')
            .where(ActiveMembers.role_id == self.moderator)
            .gino
            .all()
        )

        names = [dict(row).get('display_name') for row in rows]

        name = format_list(
            names,
            symbol='bullet',
            sort=True
        )

        embed = discord.Embed(color=self.viking.color)
        embed.add_field(name='Moderators', value=name)
        await ctx.send(embed=embed)

    @commands.command()
    async def nicknames(self, ctx):
        """
        *nicknames

        A command that displays the total number of Discord members
        with nicknames in the guild.
        """

        count = await database.func.count(ActiveMembers.nickname).gino.scalar()
        await ctx.send(f"There are {count} members with nicknames")

    @commands.command()
    async def owner(self, ctx):
        """
        *owner

        A command that mentions the owner of the Discord server.
        """

        await ctx.send(ctx.guild.owner.mention)

    @commands.command()
    @commands.cooldown(rate=1, per=30.0, type=commands.BucketType.default)
    async def ping(self, ctx):
        """
        *ping

        A command that displays the latency to the Discord server.
        """

        await ctx.send(f"Ping: {self.viking.latency * 1000:.0f} ms")


def setup(viking):
    viking.add_cog(Discord(viking))
