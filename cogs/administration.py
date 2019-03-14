import logging
import paramiko
import platform
from discord.ext import commands
from subprocess import Popen, PIPE


log = logging.getLogger(__name__)


class Administration:
    def __init__(self, viking):
        self. viking = viking

    @commands.command(hidden=True)
    @commands.is_owner()
    async def kill(self, ctx):
        """*kill

        A command that logs out of Discord, and closes
        all connections.
        """

        log.info('Viking is offline.')
        await self.viking.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def restart(self, ctx):
        """*restart

        A command that will restart my Raspberry Pi, and subsequently Viking.
        """

        if platform.system() is 'Windows':
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname='192.168.0.21', username='brayden', key_filename='private_key.pem')
            client.exec_command('sudo /home/brayden/Documents/viking/reboot.sh')
            client.close()

            log.info('Viking is restarting.')
            await self.viking.logout()

        else:
            process = Popen(['sudo', '/home/brayden/Documents/viking/reboot.sh'], stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()

            log.info('Viking is restarting.')
            await self.viking.logout()


def setup(viking):
    viking.add_cog(Administration(viking))
