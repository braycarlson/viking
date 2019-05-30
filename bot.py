import aiohttp
import discord
import logging
import os
import time
import traceback
from configparser import RawConfigParser
from datetime import datetime
from discord.ext import commands
from utilities.format import format_list


configuration = RawConfigParser()
configuration.read(os.path.join(
    os.path.dirname(__file__),
    'config.ini')
)
log = logging.getLogger(__name__)


class Viking(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or('*'),
            case_insensitive=True,
            pm_help=None,
            help_attrs=dict(hidden=True)
        )

        # Bot
        self.bot_name = configuration['bot']['name']
        self.client_id = configuration['bot'].getint('client_id')
        self.color = discord.Colour.purple()
        self.guild_id = configuration['bot'].getint('guild_id')
        self.initialize_extensions = []
        self.owner_id = configuration['bot'].getint('owner_id')
        self.root = os.path.dirname(__file__)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.start_time = time.time()
        self.token = configuration['bot']['token']

        # Role
        self.administrator = configuration['role'].getint('administrator')
        self.moderator = configuration['role'].getint('moderator')
        self.normal = configuration['role'].getint('normal')

        # Database
        self.postgresql_uri = configuration['database']['postgresql']
        self.redis_uri = configuration['database']['redis']

        # API
        self.lol_api_key = configuration['lol']['key']
        self.owm_api_key = configuration['owm']['key']
        self.trn_api_key = configuration['trn']['key']

    def get_extensions(self):
        with os.scandir(os.path.join(self.root, 'cogs')) as directory:
            for file in directory:
                if not file.name.startswith('.') and file.is_file():
                    name, extension = os.path.splitext(file.name)
                    self.initialize_extensions.append(f'cogs.{name}')

    def load_extensions(self):
        for extension in self.initialize_extensions:
            try:
                self.load_extension(extension)
            except ModuleNotFoundError as exception:
                log.warning(exception)

    async def on_command_error(self, ctx, error):
        """
        An event that is called when an error is raised while invoking
        a command.
        """

        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            await ctx.send(
                f"This command is on cooldown. "
                f"Please wait {seconds:.0f} seconds."
            )

        elif isinstance(error, commands.CommandNotFound):
            async with self.postgresql.acquire() as connection:
                query = """
                        SELECT name
                        FROM public_commands
                        WHERE levenshtein(name, $1) <= 2
                        LIMIT 5;
                        """

                suggestions = await connection.fetch(query, ctx.invoked_with)

                if len(suggestions) > 0:
                    suggestion = format_list(
                        suggestions,
                        key='name',
                        symbol='asterisk',
                        sort=False
                    )
                    embed = discord.Embed(color=self.color)
                    embed.add_field(
                        name='Command not found. Did you mean...',
                        value=suggestion
                    )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send('Command not found.')

        elif isinstance(
            error, (commands.BadArgument,
                    commands.MissingRequiredArgument,
                    commands.CheckFailure)
        ):
            pass

        else:
            traceback.print_tb(error.original.__traceback__)
            log.warning(f"{error.original.__class__.__name__} "
                        f"from {ctx.command.qualified_name}: "
                        f"{error.original}")

    async def on_connect(self):
        """
        An event that is called when the client has successfully
        connected to Discord.
        """

        log.info(f"{self.bot_name} is connected.")

    async def on_message(self, message: discord.Message):
        """
        An event that is called every time a message is recieved,
        including Viking.
        """

        if message.author.bot:
            return

        await self.process_commands(message)

    async def on_ready(self):
        """
        An event that is called when the client is done preparing data
        received from Discord.
        """

        print(f"{self.bot_name} [#{self.client_id}]")
        print(f"{datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        log.info(f"{self.bot_name} is ready.")

    def run(self):
        self.get_extensions()
        self.load_extensions()
        super().run(self.token, reconnect=True)
