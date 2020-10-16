import aiohttp
import discord
import logging
import sys
import time
import traceback
from configparser import RawConfigParser
from database.model import database, PublicCommands
from datetime import datetime
from discord.ext import commands
from pathlib import Path, PurePath
from tabulate import tabulate
from utilities.format import format_list


ROOT = PurePath(__file__).parent


configuration = RawConfigParser()
configuration.read(
    ROOT.joinpath('config.ini')
)
log = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.members = True
intents.presences = True


class Viking(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or('*'),
            case_insensitive=True,
            intents=intents,
            pm_help=None,
            help_attrs=dict(hidden=True)
        )

        # Bot
        self.bot_name = configuration['bot']['bot_name']
        self.bot_id = configuration['bot'].getint('bot_id')
        self.color = discord.Colour.purple()
        self.guild_id = configuration['bot'].getint('guild_id')
        self.initialize_extensions = []
        self.owner_id = configuration['bot'].getint('owner_id')
        self.root = Path(__file__).parent
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.start_time = time.time()
        self.token = configuration['bot']['token']

        # Role
        self.administrator = configuration['role'].getint('administrator')
        self.moderator = configuration['role'].getint('moderator')
        self.normal = configuration['role'].getint('normal')

        # Database
        self.postgresql_uri = configuration['database']['postgresql']

        # API
        self.lol_api_key = configuration['lol']['key']
        self.owm_api_key = configuration['owm']['key']
        self.rpd_api_key = configuration['rpd']['key']
        self.trn_api_key = configuration['trn']['key']
        self.wow_api_id = configuration['wow']['id']
        self.wow_api_key = configuration['wow']['key']

    def get_extensions(self):
        for path in self.root.joinpath('cogs').iterdir():
            if not path.name.startswith('.') and path.is_file():
                self.initialize_extensions.append(f'cogs.{path.stem}')

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
            rows = (
                await PublicCommands
                .select('name')
                .where(
                    database.func.levenshtein(
                        PublicCommands.name,
                        ctx.invoked_with
                    ) <= 2
                )
                .limit(5)
                .gino
                .all()
            )

            if len(rows) > 0:
                suggestions = [dict(row).get('name') for row in rows]

                suggestion = format_list(
                    suggestions,
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

        await database.set_bind(self.postgresql_uri)
        log.info(f"{self.bot_name} is connected.")

    async def on_message(self, message: discord.Message):
        """
        An event that is called every time a message is recieved,
        including Viking.
        """

        if message.author.bot or message.content.startswith('*') and message.content.endswith('*'):
            return

        await self.process_commands(message)

    async def on_ready(self):
        """
        An event that is called when the client is done preparing data
        received from Discord.
        """

        python = sys.version_info

        table = [
            ['ID', self.bot_id],
            ['Name', self.bot_name],
            ['Python', f"{python.major}.{python.minor}.{python.micro}"],
            ['Discord.py', discord.__version__],
            ['Date', datetime.now().strftime('%B %d, %Y at %I:%M %p')]
        ]

        print(tabulate(table, tablefmt='psql'))
        log.info(f"{self.bot_name} is ready.")

    def run(self):
        self.get_extensions()
        self.load_extensions()
        super().run(self.token, reconnect=True)
