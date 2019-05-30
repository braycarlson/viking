import discord
import logging
from discord.ext import commands
from utilities.format import format_list


log = logging.getLogger(__name__)


class Discord(commands.Cog):
    def __init__(self, viking):
        self.viking = viking

    @commands.command(aliases=['admins'])
    async def administrators(self, ctx):
        """
        *administrators

        A command that displays the names of the administrators in the
        guild.
        """

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    SELECT display_name
                    FROM members
                    WHERE role_id = 281951458587574282
                    """

            rows = await connection.fetch(query)
            names = format_list(
                rows,
                key='display_name',
                symbol='bullet',
                sort=True
            )

            embed = discord.Embed(color=self.viking.color)
            embed.add_field(name='Administrators', value=names)
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

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    SELECT COUNT(discord_id)
                    FROM members
                    """

            row = await connection.fetchval(query)
            await ctx.send(f"There are {row} members in this server")

    @commands.command(aliases=['mods'])
    async def moderators(self, ctx):
        """
        *moderators

        A command that displays the names of the moderators in the guild.
        """

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    SELECT display_name
                    FROM members
                    WHERE role_id = 281968300278284288
                    """

            rows = await connection.fetch(query)
            names = format_list(
                rows,
                key='display_name',
                symbol='bullet',
                sort=True
            )

            embed = discord.Embed(color=self.viking.color)
            embed.add_field(name='Moderators', value=names)
            await ctx.send(embed=embed)

    @commands.command()
    async def nicknames(self, ctx):
        """
        *nicknames

        A command that displays the total number of Discord members
        with nicknames in the guild.
        """

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    SELECT COUNT(nickname)
                    FROM members
                    WHERE nickname IS NOT NULL
                    """

            row = await connection.fetchval(query)
            await ctx.send(f"There are {row} members with nicknames")

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
