from __future__ import annotations

import aiohttp
import asyncio
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
    viking,
)
from datetime import datetime, timezone
from discord.ext import commands
from pathlib import Path
from random import SystemRandom
from sqlalchemy import func
from tabulate import tabulate
from typing import TYPE_CHECKING
from utilities.format import format_list
from utilities.time import midnight

if TYPE_CHECKING:
    from discord.app_commands import AppCommandError


path = Path(__file__).parent.joinpath('config.ini')

configuration = RawConfigParser()
configuration.read(path)

log = logging.getLogger(__name__)


class Viking(commands.Bot):
    def __init__(self):
        allowed_mentions = discord.AllowedMentions(
            everyone=False,
            roles=False,
            users=True,
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
            help_attrs={'hidden': True},
        )

        # Bot
        self.bot_name = configuration['bot']['bot_name']
        self.bot_id = configuration['bot'].getint('bot_id')
        self.color = discord.Colour.purple()
        self.initialize_extensions = []
        self.owner_id = configuration['bot'].getint('owner_id')
        self.random = SystemRandom()
        self.root = Path(__file__).parent
        self.start_time = time.time()
        self.token = configuration['bot']['token']

        # Directories
        self.images = self.root.joinpath('images')
        self.champion = self.images.joinpath('lol/champion')
        self.item = self.images.joinpath('lol/item')
        self.rune = self.images.joinpath('lol/rune')
        self.spell = self.images.joinpath('lol/spell')

        self.logs = self.root.joinpath('logs')
        self.sound = self.root.joinpath('sound')

        # Database
        self.identifier = ContextVar(
            '863292513141522433',
            default='863292513141522433',
        )
        self.uri = configuration['database']['postgresql']

        # API
        self.lol_api_key = configuration['lol']['key']
        self.lol_api_url = configuration['lol']['url']
        self.owm_api_key = configuration['owm']['key']
        self.owm_api_url = configuration['owm']['url']
        self.rpd_api_key = configuration['rpd']['key']
        self.trn_api_key = configuration['trn']['key']
        self.wow_api_id = configuration['wow']['id']
        self.wow_api_key = configuration['wow']['key']

    @property
    def guild(self) -> str:
        identifier = self.identifier.get()

        guild = Guild()
        return guild.get(identifier)

    async def update(self, identifier: str) -> None:
        identifier = str(identifier)
        self.identifier.set(identifier)

    async def purge(self) -> None:
        """
        A function that purges all messages from the spam channel at
        midnight.
        """

        while not self.is_closed():
            time = midnight()
            await asyncio.sleep(time)

            for guild in self.guilds:
                for channel in guild.text_channels:
                    if channel.name == 'spam':
                        await channel.purge()

    async def setup_hook(self) -> None:
        self.loop.create_task(
            self.purge()
        )

        await command.set_bind(self.uri + 'command')
        await lol.set_bind(self.uri + 'lol')
        await nac.set_bind(self.uri + 'nac')
        await viking.set_bind(self.uri + 'viking')

        self.session = aiohttp.ClientSession(loop=self.loop)

    def get_extensions(self) -> None:
        for path in self.root.joinpath('cogs').iterdir():
            if not path.name.startswith('.') and path.is_file():
                self.initialize_extensions.append(f'cogs.{path.stem}')

    async def load_extensions(self) -> None:
        for extension in self.initialize_extensions:
            try:
                await self.load_extension(extension)
            except ModuleNotFoundError as exception:
                log.warning(exception)

    async def process_commands(self, message: str) -> None:
        ctx = await self.get_context(message)

        if message.guild is not None:
            await self.update(message.guild.id)

        await self.invoke(ctx)

    async def on_command_error(
        self,
        ctx: commands.Context,
        error: AppCommandError
    ) -> None:
        """
        An event that is called when an error is raised while invoking
        a command.
        """

        match error:
            case commands.CommandOnCooldown():
                minutes, seconds = divmod(error.retry_after, 60)

                await ctx.send(
                    f"This command is on cooldown. "
                    f"Please wait {seconds:.0f} seconds."
                )

            case commands.CommandNotFound():
                rows = (
                    await Public
                    .select('name')
                    .where(func.levenshtein(Public.name, ctx.invoked_with) < 3)
                    .limit(5)
                    .gino
                    .all()
                )

                if len(rows) == 0:
                    await ctx.send('Command not found.')
                    return

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

            case (
                commands.CheckFailure(),
                commands.MissingPermissions(),
                commands.MissingRole()
            ):
                await ctx.send('You do not have permission to use this command.')

            case (
                commands.BadArgument(),
                commands.MissingRequiredArgument()
            ):
                return

            case _:
                traceback.print_tb(error.__traceback__)

                message = f"{error.__class__.__name__} from {ctx.command.qualified_name}."
                log.warning(message)

                if hasattr(error, 'original'):
                    log.warning(error.original)

    async def on_connect(self) -> None:
        """
        An event that is called when the client has successfully
        connected to Discord.
        """

        message = f"{self.bot_name} is connected."
        log.info(message)

    async def on_message(self, message: str) -> None:
        """
        An event that is called every time a message is recieved,
        including Viking.
        """

        condition = (
            message.author.bot or
            message.content.endswith('*') or
            message.content.startswith('*') and
            message.content.endswith('*') or
            message.content.startswith('**') or
            message.content.endswith('**') or
            message.content.startswith('**') and
            message.content.endswith('**')
        )

        if condition:
            return

        await self.process_commands(message)

    async def on_ready(self) -> None:
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
            ['Date', datetime.now(tz=timezone.utc).strftime('%B %d, %Y at %I:%M %p')]
        ]

        display = tabulate(table, tablefmt='psql')
        print(display)

        message = f"{self.bot_name} is ready."
        log.info(message)

    async def start(self) -> None:
        self.get_extensions()
        await self.load_extensions()
        await super().start(self.token, reconnect=True)
