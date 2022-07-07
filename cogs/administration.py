import database.engine
import logging
import paramiko

from bot import ROOT
from configparser import RawConfigParser
from discord.ext import commands


log = logging.getLogger(__name__)
configuration = RawConfigParser()
configuration.read(
    ROOT.joinpath('config.ini')
)


class Administration(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.root = viking.root
        self.crontab_path = self.root.joinpath('logs/crontab.txt')
        self.log_path = self.root.joinpath('logs/viking.log')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def kill(self, ctx):
        """
        *kill

        A command that closes all database connections, and logs out
        of Discord.
        """

        await ctx.message.delete()

        log.info('Viking is offline.')

        await database.engine.command.pop_bind().close()
        await database.engine.lol.pop_bind().close()

        guild = database.engine.Guild()

        for engine in guild.generate('engine'):
            await engine.pop_bind().close()

        await self.viking.session.close()
        await self.viking.close()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def restart(self, ctx):
        """
        *restart

        A command that restarts my Raspberry Pi and Viking.
        """

        await ctx.message.delete()

        client = paramiko.SSHClient()
        client.load_host_keys(
            self.root.joinpath('known_hosts')
        )
        client.connect(
            hostname=configuration['paramiko']['hostname'],
            username=configuration['paramiko']['username'],
            password=configuration['paramiko']['password'],
        )
        client.exec_command('sudo /sbin/reboot')
        client.close()

        log.info('Viking is restarting.')

        await database.engine.command.pop_bind().close()
        await database.engine.lol.pop_bind().close()

        guild = database.engine.Guild()

        for engine in guild.generate('engine'):
            await engine.pop_bind().close()

        await self.viking.session.close()
        await self.viking.close()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def wipe(self, ctx):
        """
        *wipe

        A command that clears all log files.
        """

        await ctx.message.delete()

        self.crontab_path.open('w', encoding='utf-8').close()
        self.log_path.open('w', encoding='utf-8').close()


async def setup(viking):
    administration = Administration(viking)
    await viking.add_cog(administration)
