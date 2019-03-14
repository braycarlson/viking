import discord
import logging
from discord.ext import commands


log = logging.getLogger(__name__)


class Moderation:
    def __init__(self, viking):
        self. viking = viking

    @commands.command(hidden=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_any_role('Administrator', 'Moderator')
    async def ban(self, ctx, *, member: discord.User):
        """*ban <member>

        A command that bans a member by name, mention or ID.
        """

        await ctx.guild.ban(member)
        log.info(f"{ctx.author} banned {member}")

    @commands.command(hidden=True)
    @commands.has_any_role('Administrator', 'Moderator')
    async def clear(self, ctx, amount: int):
        """*clear <amount>

        A command that will clear a specified amount of messages from a
        text channel.
        """

        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"`{len(deleted)}` messages cleared.", delete_after=5)

    @commands.command(hidden=True)
    @commands.bot_has_permissions(kick_members=True)
    @commands.has_any_role('Administrator', 'Moderator')
    async def kick(self, ctx, member: discord.User):
        """*kick <member>

        A command that kicks a member by name, mention or ID.
        """

        await member.kick()
        log.info(f"{ctx.author} kicked {member}")

    @commands.command(hidden=True)
    @commands.has_any_role('Administrator', 'Moderator')
    async def load(self, ctx, *, extension):
        """*load <extension>

        A command that will load an extension.
        """

        extension = f"cogs.{extension}"

        try:
            self.viking.load_extension(extension)
            await ctx.send(f"`{extension}` was loaded.", delete_after=5)
        except ModuleNotFoundError:
            await ctx.send(f"`{extension}` does not exist.", delete_after=5)

    @commands.command(hidden=True)
    @commands.has_any_role('Administrator', 'Moderator')
    async def purge(self, ctx):
        """*purge

        A command that will purge all messages from a text channel.
        """

        await ctx.channel.purge()

    @commands.command(hidden=True)
    @commands.has_any_role('Administrator', 'Moderator')
    async def reload(self, ctx, *, extension):
        """*reload <extension>

        A command that will reload an extension.
        """

        extension = f"cogs.{extension}"

        try:
            self.viking.unload_extension(extension)
            self.viking.load_extension(extension)
            await ctx.send(f"`{extension}` was successfully reloaded.", delete_after=5)
        except ModuleNotFoundError:
            await ctx.send(f"`{extension}` does not exist.", delete_after=5)

    @commands.command(hidden=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_any_role('Administrator', 'Moderator')
    async def unban(self, ctx, *, member):
        """*unban <member>

        A command that unbans a member by name, mention or ID.
        """

        bans = await ctx.guild.bans()

        try:
            member_id = int(member, base=10)
        except ValueError:
            banned = discord.utils.get(bans, user__name=member)
        else:
            banned = discord.utils.get(bans, user__id=member_id)

        if banned:
            await ctx.guild.unban(banned.user)
            log.info(f"{ctx.author} unbanned {banned.user}")

    @commands.command(hidden=True)
    @commands.has_any_role('Administrator', 'Moderator')
    async def unload(self, ctx, *, extension):
        """*unload <extension>

        A command that will unload an extension.
        """

        extension = f"cogs.{extension}"

        if extension in self.viking.extensions.keys():
            self.viking.unload_extension(extension)
            await ctx.send(f"`{extension}` was successfully unloaded.", delete_after=5)
        else:
            await ctx.send(f"`{extension}` does not exist.", delete_after=5)


def setup(viking):
    viking.add_cog(Moderation(viking))
