from __future__ import annotations

import database.engine
import logging
import paramiko

from bot import configuration, Viking
from discord.ext import commands
from pathlib import Path


log = logging.getLogger(__name__)


class Administration(commands.Cog):
    def __init__(self, viking: Viking):
        self.viking = viking
        self.logs = viking.logs
        self.root = viking.root

    @commands.command(hidden=True)
    @commands.is_owner()
    async def kill(self, ctx: commands.Context) -> None:
        """
        *kill

        A command that closes all database connections, and logs out
        of Discord.
        """

        await ctx.message.delete()

        log.info('Viking is offline.')

        guild = database.engine.Guild()

        for engine in guild.generate('engine'):
            await engine.pop_bind().close()

        await database.engine.command.pop_bind().close()
        await database.engine.lol.pop_bind().close()

        await self.viking.session.close()
        await self.viking.close()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def restart(self, ctx: commands.Context) -> None:
        """
        *restart

        A command that restarts my Raspberry Pi and Viking.
        """

        await ctx.message.delete()

        client = paramiko.SSHClient()

        path = self.root.joinpath('known_hosts')
        client.load_host_keys(path)

        client.connect(
            hostname=configuration['paramiko']['hostname'],
            username=configuration['paramiko']['username'],
            password=configuration['paramiko']['password'],
        )

        client.exec_command('sudo /sbin/reboot')
        client.close()

        log.info('Viking is restarting.')

        guild = database.engine.Guild()

        for engine in guild.generate('engine'):
            await engine.pop_bind().close()

        await database.engine.command.pop_bind().close()
        await database.engine.lol.pop_bind().close()

        await self.viking.session.close()
        await self.viking.close()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def wake(self, ctx: commands.Context) -> None:
        """
        *wake

        A command that wakes a PC via magic packet
        """

        await ctx.message.delete()

        client = paramiko.SSHClient()

        path = self.root.joinpath('known_hosts')
        client.load_host_keys(path)

        client.connect(
            hostname=configuration['paramiko']['hostname'],
            username=configuration['paramiko']['username'],
            password=configuration['paramiko']['password'],
        )

        path = Path('/home/brayden/Documents/wol.sh')
        command = f"bash {path}"

        client.exec_command(command)
        client.close()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def wipe(self, ctx: commands.Context) -> None:
        """
        *wipe

        A command that clears all log files.
        """

        await ctx.message.delete()

        log = self.logs.glob('*.log')
        txt = self.logs.glob('*.txt')

        for file in log:
            file.open('w', encoding='utf-8').close()

        for file in txt:
            file.open('w', encoding='utf-8').close()


async def setup(viking: Viking) -> None:
    administration = Administration(viking)
    await viking.add_cog(administration)
