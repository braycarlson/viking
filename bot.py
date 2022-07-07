import aiohttp
import discord
import logging
import sys
import time
import traceback

from configparser import RawConfigParser
from contextvars import ContextVar
from database.command import Public
from database.engine import (
    command,
    Guild,
    lol,
    nac,
    viking
)
from datetime import datetime
from discord.ext import commands
from pathlib import Path
from tabulate import tabulate
from utilities.format import format_list


ROOT = Path(__file__).parent


configuration = RawConfigParser()
configuration.read(
    ROOT.joinpath('config.ini')
)
log = logging.getLogger(__name__)


class Viking(commands.Bot):
    def __init__(self):
        allowed_mentions = discord.AllowedMentions(
            everyone=False,
            roles=False,
            users=True
        )

        intents = discord.Intents(
            bans=True,
            emojis=True,
            guilds=True,
            members=True,
            message_content=True,
            messages=True,
            reactions=True,
            voice_states=True,
        )

        super().__init__(
            allowed_mentions=allowed_mentions,
            command_prefix=commands.when_mentioned_or('*'),
            case_insensitive=True,
            enable_debug_events=True,
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
        self.start_time = time.time()
        self.token = configuration['bot']['token']

        # Role
        self.administrator = configuration['role'].getint('administrator')
        self.moderator = configuration['role'].getint('moderator')
        self.normal = configuration['role'].getint('normal')

        # Database
        self.identifier = ContextVar(
            '863292513141522433',
            default='863292513141522433'
        )
        self.uri = configuration['database']['postgresql']

        # API
        self.lol_api_url = configuration['lol']['api']
        self.lol_api_key = configuration['lol']['key']
        self.owm_api_key = configuration['owm']['key']
        self.rpd_api_key = configuration['rpd']['key']
        self.trn_api_key = configuration['trn']['key']
        self.wow_api_id = configuration['wow']['id']
        self.wow_api_key = configuration['wow']['key']

    @property
    def guild(self):
        identifier = self.identifier.get()
        guild = Guild()
        return guild.get(identifier)

    async def update(self, identifier):
        identifier = str(identifier)
        self.identifier.set(identifier)

    async def setup_hook(self):
        await command.set_bind(self.uri + 'command')
        await lol.set_bind(self.uri + 'lol')
        await nac.set_bind(self.uri + 'nac')
        await viking.set_bind(self.uri + 'viking')

        self.session = aiohttp.ClientSession(loop=self.loop)

    def get_extensions(self):
        for path in self.root.joinpath('cogs').iterdir():
            if not path.name.startswith('.') and path.is_file():
                self.initialize_extensions.append(f'cogs.{path.stem}')

    async def load_extensions(self):
        for extension in self.initialize_extensions:
            try:
                await self.load_extension(extension)
            except ModuleNotFoundError as exception:
                log.warning(exception)

    async def process_commands(self, message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        await self.update(message.guild.id)
        await self.invoke(ctx)

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
                await Public
                .select('name')
                .where(
                    command.func.levenshtein(
                        Public.name,
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

            log.warning(
                f"{error.original.__class__.__name__} "
                f"from {ctx.command.qualified_name}: "
                f"{error.original}"
            )

    async def on_connect(self):
        """
        An event that is called when the client has successfully
        connected to Discord.
        """

        log.info(f"{self.bot_name} is connected.")

    async def on_message(self, message):
        """
        An event that is called every time a message is recieved,
        including Viking.
        """

        condition = (
            message.author.bot or
            message.content.startswith('*') and message.content.endswith('*') or
            message.content.startswith('**') and message.content.endswith('**')
        )

        if condition:
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

    async def start(self):
        self.get_extensions()
        await self.load_extensions()
        await super().start(self.token, reconnect=True)
