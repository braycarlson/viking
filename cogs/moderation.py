import asyncio
import discord
import logging

from database.command import Hidden
from discord.ext import commands
from utilities.format import format_list
from utilities.member import MemberInterface
from utilities.time import timeout


log = logging.getLogger(__name__)


class Moderation(commands.Cog):
    def __init__(self, viking):
        self.viking = viking

    async def chat_restrict(self):
        """
        A function that changes Discord permissions to chat restrict
        a member.
        """

        overwrite = discord.PermissionOverwrite()

        overwrite.send_messages = False
        overwrite.send_tts_messages = False
        overwrite.add_reactions = False

        return overwrite

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(move_members=True)
    @commands.has_guild_permissions(move_members=True)
    async def afk(self, ctx, identifier):
        """
        *afk <identifier>

        A command that moves a member by name, nickname or ID to a
        designated voice channel.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = ctx.guild.get_member(discord_id)

        try:
            await member.edit(voice_channel=ctx.guild.afk_channel)
        except discord.HTTPException:
            await ctx.send(f"{member} could not be moved to Valhalla.")
        else:
            log.info(f"{ctx.author} moved {member} to Valhalla.")

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx, *, identifier):
        """
        *ban <identifier>

        A command that bans a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = self.viking.get_user(discord_id)

        try:
            await ctx.guild.ban(member)
        except discord.HTTPException:
            await ctx.send(f"{member} could not be banned.")
        else:
            log.info(f"{ctx.author} banned {member}.")

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    @commands.has_guild_permissions(manage_messages=True)
    async def clear(self, ctx, limit: int):
        """
        *clear <limit>

        A command that clears a specified amount of messages from a
        text channel.
        """

        await ctx.message.delete()
        await ctx.channel.purge(limit=limit)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def deafen(self, ctx, identifier):
        """
        *deafen <identifier>

        A command that deafens a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = ctx.guild.get_member(discord_id)

        try:
            await member.edit(deafen=True)
        except discord.HTTPException:
            await ctx.send(f"{member} could not be deafened.")
        else:
            log.info(f"{ctx.author} deafened {member}.")

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(move_members=True)
    @commands.has_guild_permissions(move_members=True)
    async def disconnect(self, ctx, identifier):
        """
        *disconnect <identifier>

        A command that disconnects a member from a voice channel by name,
        nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = ctx.guild.get_member(discord_id)

        try:
            await member.edit(voice_channel=None)
        except discord.HTTPException:
            await ctx.send(f"{member} could not be disconnected.")
        else:
            log.info(f"{ctx.author} disconnected {member}.")

    @commands.command(hidden=True)
    async def hidden(self, ctx):
        """
        *hidden

        A command that displays hidden commands that are available
        for administrators/moderators to use.
        """

        rows = await Hidden.select('name').gino.all()
        commands = [dict(row).get('name') for row in rows]

        command = format_list(
            commands,
            symbol='asterisk',
            sort=True
        )

        embed = discord.Embed(color=self.viking.color)
        embed.add_field(name='Hidden Commands', value=command)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(kick_members=True)
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx, identifier):
        """
        *kick <identifier>

        A command that kicks a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = self.viking.get_user(discord_id)

        try:
            await ctx.guild.kick(member)
        except discord.HTTPException:
            await ctx.send(f"{member} could not be kicked.")
        else:
            log.info(f"{ctx.author} kicked {member}.")

    @commands.command(hidden=True)
    async def load(self, ctx, *, extension):
        """
        *load <extension>

        A command that loads an extension.
        """

        extension = f"cogs.{extension}"

        try:
            await self.viking.load_extension(extension)
        except ModuleNotFoundError:
            await ctx.send(f"`{extension}` does not exist.")
        else:
            await ctx.send(f"`{extension}` was successfully loaded.")

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def mute(self, ctx, identifier):
        """
        *mute <identifier>

        A command that mutes a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = ctx.guild.get_member(discord_id)

        try:
            await member.edit(mute=True)
        except discord.HTTPException:
            await ctx.send(f"{member} could not be muted.")
        else:
            log.info(f"{ctx.author} muted {member}.")

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def purge(self, ctx):
        """
        *purge

        A command that purges all messages from a text channel.
        """

        await ctx.channel.purge()

    @commands.command(hidden=True)
    async def reload(self, ctx, *, extension):
        """
        *reload <extension>

        A command that reloads an extension.
        """

        extension = f"cogs.{extension}"

        try:
            await self.viking.unload_extension(extension)
            await self.viking.load_extension(extension)
        except ModuleNotFoundError:
            await ctx.send(f"`{extension}` does not exist.")
        else:
            await ctx.send(f"`{extension}` was successfully reloaded.")

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def restrict(self, ctx, *, identifier):
        """
        *restrict <identifier>

        A command that restricts a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = ctx.guild.get_member(discord_id)

        try:
            for channel in ctx.guild.text_channels:
                overwrite = await self.chat_restrict()
                await channel.set_permissions(member, overwrite=overwrite)
        except discord.HTTPException:
            await ctx.send(f"{member} could not be chat-restricted.")
        else:
            log.info(f"{ctx.author} chat-restricted {member}.")

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def softdeafen(self, ctx, seconds: int, *, identifier):
        """
        *softdeafen <seconds> <identifier>

        A command that soft-deafens a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = ctx.guild.get_member(discord_id)

        try:
            if seconds <= 3600:
                await member.edit(deafen=True)
            else:
                await ctx.send('A soft-deafen must be less than an hour.')
        except discord.HTTPException:
            await ctx.send(f"{member} could not be soft-deafened.")
        else:
            log.info(f"{ctx.author} soft-deafened {member}.")

            while not self.viking.is_closed():
                time = timeout(seconds=seconds)
                await asyncio.sleep(time)

                await member.edit(deafen=False)
                break

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def softmute(self, ctx, seconds: int, *, identifier):
        """
        *softmute <seconds> <identifier>

        A command that soft-mutes a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = ctx.guild.get_member(discord_id)

        try:
            if seconds <= 3600:
                await member.edit(mute=True)
            else:
                await ctx.send('A soft-mute must be less than an hour.')
        except discord.HTTPException:
            await ctx.send(f"{member} could not be soft-muted.")
        else:
            log.info(f"{ctx.author} soft-muted {member}.")

            while not self.viking.is_closed():
                time = timeout(seconds=seconds)
                await asyncio.sleep(time)

                await member.edit(mute=False)
                break

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def softrestrict(self, ctx, seconds: int, *, identifier):
        """
        *softrestrict <seconds> <identifier>

        A command that soft-restricts a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = ctx.guild.get_member(discord_id)

        try:
            if seconds <= 3600:
                for channel in ctx.guild.text_channels:
                    overwrite = await self.chat_restrict()
                    await channel.set_permissions(
                        member,
                        overwrite=overwrite
                    )
            else:
                await ctx.send('A soft-restrict must be less than an hour.')
        except discord.HTTPException:
            await ctx.send(f"{member} could not be chat-restricted.")
        else:
            log.info(f"{ctx.author} chat-restricted {member}.")

            while not self.viking.is_closed():
                time = timeout(seconds=seconds)
                await asyncio.sleep(time)

                for channel in ctx.guild.text_channels:
                    await channel.set_permissions(member, overwrite=None)

                break

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx, *, identifier):
        """
        *unban <identifier>

        A command that unbans a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = await self.viking.fetch_user(discord_id)

        try:
            await ctx.guild.unban(member)
        except discord.HTTPException:
            await ctx.send(f"{member} could not be unbanned.")
        else:
            log.info(f"{ctx.author} unbanned {member}.")

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def undeafen(self, ctx, identifier):
        """
        *undeafen <identifier>

        A command that undeafens a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = ctx.guild.get_member(discord_id)

        try:
            await member.edit(deafen=False)
        except discord.HTTPException:
            await ctx.send(f"{member} could not be undeafened.")
        else:
            log.info(f"{ctx.author} undeafened {member}.")

    @commands.command(hidden=True)
    async def unload(self, ctx, *, extension):
        """
        *unload <extension>

        A command that unloads an extension.
        """

        extension = f"cogs.{extension}"

        try:
            await self.viking.unload_extension(extension)
        except commands.ExtensionNotLoaded:
            await ctx.send(f"`{extension}` is not loaded or does not exist.")
        else:
            await ctx.send(f"`{extension}` was successfully unloaded.")

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def unmute(self, ctx, identifier):
        """
        *unmute <identifier>

        A command that unmutes a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = ctx.guild.get_member(discord_id)

        try:
            await member.edit(mute=False)
        except discord.HTTPException:
            await ctx.send(f"{member} could not be unmuted.")
        else:
            log.info(f"{ctx.author} unmuted {member}.")

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def unrestrict(self, ctx, *, identifier):
        """
        *unrestrict <identifier>

        A command that unrestricts a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = ctx.guild.get_member(discord_id)

        try:
            for channel in ctx.guild.text_channels:
                await channel.set_permissions(member, overwrite=None)
        except discord.HTTPException:
            await ctx.send(f"{member} could not be unrestricted.")
        else:
            log.info(f"{ctx.author} unrestricted {member}.")


async def setup(viking):
    moderation = Moderation(viking)
    await viking.add_cog(moderation)
