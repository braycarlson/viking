import aiohttp
import logging
import os
import time
import traceback
from configparser import RawConfigParser
from datetime import datetime
from discord import Colour
from discord.ext import commands


configuration = RawConfigParser()
configuration.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
log = logging.getLogger(__name__)


class Viking(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('*'),
                         case_insensitive=True,
                         pm_help=None,
                         help_attrs=dict(hidden=True))

        self.bot_name = configuration['bot']['name']
        self.client_id = configuration['bot'].getint('client_id')
        self.color = Colour.purple()
        self.inital_extensions = []
        self.lol_api_key = configuration['lol']['key']
        self.owm_api_key = configuration['owm']['key']
        self.owner_id = configuration['bot'].getint('owner_id')
        self.path = os.path.dirname(__file__)
        self.postgresql_uri = configuration['database']['postgresql']
        self.redis_uri = configuration['database']['redis']
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.start_time = time.time()
        self.token = configuration['bot']['token']
        self.trn_api_key = configuration['trn']['key']

    def get_extensions(self):
        with os.scandir(os.path.join(self.path, 'cogs')) as directory:
            for file in directory:
                if not file.name.startswith('.') and file.is_file():
                    name, extension = os.path.splitext(file.name)
                    self.inital_extensions.append(f'cogs.{name}')

    def load_extensions(self):
        for extension in self.inital_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                log.warning(e)

    async def on_command_error(self, ctx, error):
        """on_command_error(self, ctx, error)

        An event that is called when an error is
        raised while invoking a command.
        """

        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            await ctx.send(f"This command is on cooldown. "
                           f"Please wait {seconds:.0f} seconds.")

        elif isinstance(error, commands.CommandNotFound):
            async with self.postgresql.acquire() as connection:
                query = """
                        SELECT name
                        FROM commands
                        WHERE levenshtein(name, $1) <= 2
                        LIMIT 5;
                        """

                suggestions = await connection.fetch(query, ctx.invoked_with)

                if len(suggestions) >= 1:
                    await ctx.send('Command not found. Did you mean...')
                    for index, suggestion in enumerate(suggestions, 1):
                        await ctx.send(f"{index}) `*{suggestion['name']}`")
                else:
                    await ctx.send(f"`*{ctx.invoked_with}` is not a command.")

        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"A bad argument was used in this command.",
                           delete_after=5)

        else:
            traceback.print_tb(error.original.__traceback__)
            log.warning(f"{error.original.__class__.__name__} "
                        f"from {ctx.command.qualified_name}: "
                        f"{error.original}")

    async def on_connect(self):
        """on_connect(self)

        An event that is called when the client has
        successfully connected to Discord.
        """

        log.info(f"{self.bot_name} is connected.")

    async def on_message(self, message):
        """on_message(self, message)

        An event that is called every time a
        message is recieved including Viking.
        """

        if message.author.bot:
            return

        await self.process_commands(message)

    async def on_ready(self):
        """on_ready(self)

        An event that is called when the client is
        done preparing data received from Discord.
        """

        print(f"{self.bot_name} [#{self.client_id}]")
        print(f"{datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        log.info(f"{self.bot_name} is ready.")

    def run(self):
        self.get_extensions()
        self.load_extensions()
        super().run(self.token, reconnect=True)
