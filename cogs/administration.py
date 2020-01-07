import logging
import os
import paramiko
from configparser import RawConfigParser
from database.model import database
from discord.ext import commands


log = logging.getLogger(__name__)
configuration = RawConfigParser()
configuration.read(os.path.join(
    os.path.dirname(
        os.path.dirname(__file__)
    ),
    'config.ini')
)


class Administration(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.crontab_path = os.path.join(
            self.viking.root,
            'logs/crontab.txt'
        )
        self.log_path = os.path.join(
            self.viking.root,
            'logs/viking.log'
        )
        self.session = viking.session

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
        await database.pop_bind().close()
        await self.viking.session.close()
        await self.viking.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def restart(self, ctx):
        """
        *restart

        A command that restarts my Raspberry Pi and subsequently Viking.
        """

        await ctx.message.delete()

        client = paramiko.SSHClient()
        client.load_host_keys(
            os.path.join(
                self.viking.root,
                'known_hosts'
            )
        )
        client.connect(
            hostname=configuration['paramiko']['hostname'],
            username=configuration['paramiko']['username'],
            password=configuration['paramiko']['password'],
        )
        client.exec_command('sudo /sbin/reboot')
        client.close()

        log.info('Viking is restarting.')
        await database.pop_bind().close()
        await self.viking.session.close()
        await self.viking.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def wipe(self, ctx):
        """
        *wipe

        A command that clears all log files.
        """

        await ctx.message.delete()
        open(self.crontab_path, 'w').close()
        open(self.log_path, 'w').close()


def setup(viking):
    viking.add_cog(Administration(viking))
