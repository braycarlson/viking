from __future__ import annotations

import logging

import paramiko

from typing_extensions import TYPE_CHECKING

from discord.ext import commands

from admin import embeds
from core.config import configuration
from core.db.command import CommandRepository
from core.db.registry import databases

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from bot import Viking


log = logging.getLogger(__name__)


class Administration(commands.Cog):
    def __init__(self, viking: Viking) -> None:
        self.viking = viking

    @property
    def repository(self) -> CommandRepository:
        return CommandRepository(databases.command.session)

    def _ssh_command_execute(self, command: str) -> None:
        client = paramiko.SSHClient()

        path = self.viking.root.joinpath('known_hosts')
        client.load_host_keys(path)

        client.connect(
            hostname=configuration['paramiko']['hostname'],
            username=configuration['paramiko']['username'],
            password=configuration['paramiko']['password'],
        )

        client.exec_command(command)
        client.close()

    def _stop_signal(self) -> None:
        path = self.viking.root.joinpath('.stop')
        path.touch()

    # Commands

    @commands.command(hidden=True)
    @commands.has_guild_permissions(manage_guild=True)
    async def hidden(self, ctx: Context) -> None:
        """
        *hidden

        A command that displays hidden commands that are available
        for administrators/moderators to use.
        """

        rows = await self.repository.hidden_names_get()

        embed = embeds.hidden_embed(rows, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def kill(self, ctx: Context) -> None:
        """
        *kill

        A command that closes all database connections, and logs out
        of Discord.
        """

        await ctx.message.delete()

        message = 'Viking is offline.'
        log.info(message)

        self._stop_signal()

        await self.viking.close()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx: Context, *, extension: str) -> None:
        """
        *load <extension>

        A command that loads an extension.
        """

        try:
            await self.viking.load_extension(extension)
        except commands.ExtensionNotFound:
            message = f'`{extension}` does not exist.'
            await ctx.send(message)
        except commands.ExtensionAlreadyLoaded:
            message = f'`{extension}` is already loaded.'
            await ctx.send(message)
        except commands.ExtensionError:
            message = f'`{extension}` could not be loaded.'
            await ctx.send(message)

            log.exception(message)
        else:
            message = f'`{extension}` was successfully loaded.'
            await ctx.send(message)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx: Context, *, extension: str) -> None:
        """
        *reload <extension>

        A command that reloads an extension.
        """

        try:
            await self.viking.reload_extension(extension)
        except commands.ExtensionNotFound:
            message = f'`{extension}` does not exist.'
            await ctx.send(message)
        except commands.ExtensionNotLoaded:
            message = f'`{extension}` is not loaded.'
            await ctx.send(message)
        except commands.ExtensionError:
            message = f'`{extension}` could not be reloaded.'
            await ctx.send(message)

            log.exception(message)
        else:
            message = f'`{extension}` was successfully reloaded.'
            await ctx.send(message)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def respawn(self, ctx: Context) -> None:
        """
        *respawn

        A command that restarts Viking without rebooting the Raspberry
        Pi. The run.sh wrapper relaunches run.py on any exit unless the
        .stop sentinel exists, so a clean shutdown is enough.
        """

        await ctx.message.delete()

        message = 'Viking is respawning.'
        log.info(message)

        await self.viking.close()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def restart(self, ctx: Context) -> None:
        """
        *restart

        A command that restarts my Raspberry Pi and Viking.
        """

        await ctx.message.delete()

        await self.viking.loop.run_in_executor(
            None,
            self._ssh_command_execute,
            'sudo /sbin/reboot'
        )

        message = 'Viking is restarting.'
        log.info(message)

        await self.viking.close()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(self, ctx: Context, guild: str | None = None) -> None:
        """
        *sync <~>

        A command that synchronizes the application command tree. Pass no
        argument for a global sync, or "~" to sync the current guild for
        instant testing.
        """

        if guild == '~':
            self.viking.tree.copy_global_to(guild=ctx.guild)
            synced = await self.viking.tree.sync(guild=ctx.guild)
            message = f'Synced {len(synced)} command(s) to this server.'
        else:
            synced = await self.viking.tree.sync()
            message = f'Synced {len(synced)} command(s) globally.'

        await ctx.send(message)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx: Context, *, extension: str) -> None:
        """
        *unload <extension>

        A command that unloads an extension.
        """

        try:
            await self.viking.unload_extension(extension)
        except commands.ExtensionNotLoaded:
            message = f'`{extension}` is not loaded or does not exist.'
            await ctx.send(message)
        else:
            message = f'`{extension}` was successfully unloaded.'
            await ctx.send(message)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def wake(self, ctx: Context) -> None:
        """
        *wake

        A command that wakes a PC via magic packet.
        """

        await ctx.message.delete()

        command = configuration['paramiko'].get('wake_command')

        if not command:
            message = 'No `wake_command` is set in the `[paramiko]` configuration.'
            await ctx.send(message)

            return

        await self.viking.loop.run_in_executor(
            None,
            self._ssh_command_execute,
            command
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def wipe(self, ctx: Context) -> None:
        """
        *wipe

        A command that clears all log files.
        """

        await ctx.message.delete()

        log_files = self.viking.logs.glob('*.log')
        text_files = self.viking.logs.glob('*.txt')

        for file in log_files:
            file.write_text('', encoding='utf-8')

        for file in text_files:
            file.write_text('', encoding='utf-8')


async def setup(viking: Viking) -> None:
    administration = Administration(viking)
    await viking.add_cog(administration)
