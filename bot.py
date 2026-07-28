from __future__ import annotations

import logging
import sys
import time
import traceback

import aiohttp
import discord

from contextvars import ContextVar
from datetime import datetime, time as time_of_day, UTC
from math import ceil
from pathlib import Path
from random import SystemRandom

from discord import app_commands
from discord.ext import commands, tasks
from tabulate import tabulate

from core import embeds
from core.config import configuration
from core.db.command import CommandRepository
from core.db.engine import engine_initialize
from core.db.registry import databases, DatabaseConfiguration


log = logging.getLogger(__name__)

PURGE_CHANNEL = 'spam'
PURGE_MESSAGES_MAX = 1000


class GuildContextError(commands.CheckFailure):
    pass


class Viking(commands.Bot):
    def __init__(self) -> None:
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
            presences=True,
            reactions=True,
            voice_states=True,
        )

        super().__init__(
            allowed_mentions=allowed_mentions,
            command_prefix=commands.when_mentioned_or('*'),
            case_insensitive=True,
            intents=intents,
        )

        # Bot
        self.bot_name = configuration['bot']['bot_name']
        self.bot_identifier = configuration['bot'].getint('bot_id')
        self.colour = discord.Colour.purple()
        self.extension_names: list[str] = []
        self.owner_id = configuration['bot'].getint('owner_id')
        self.random = SystemRandom()
        self.root = Path(__file__).parent
        self.session: aiohttp.ClientSession | None = None
        self.start_time = time.time()
        self.token = configuration['bot']['token']

        # Directories
        self.images = self.root.joinpath('images')
        self.champion = self.images.joinpath('lol/champion')

        self.logs = self.root.joinpath('.logs')
        self.sound = self.root.joinpath('.sound')

        # Database
        self.identifier: ContextVar[str | None] = ContextVar(
            'identifier',
            default=None,
        )

        self.uri = configuration['database']['postgresql']

        # API
        self.lol_api_key = configuration['lol']['key']
        self.lol_api_url = configuration['lol']['url']
        self.owm_api_key = configuration['owm']['key']
        self.owm_api_url = configuration['owm']['url']

    @property
    def guild(self) -> DatabaseConfiguration:
        identifier = self.identifier.get()

        if identifier is None:
            database = None
        else:
            database = databases.guild(identifier)

        if database is None:
            message = f'No database is registered for the guild: {identifier}'
            raise GuildContextError(message)

        return database

    async def _identifier_set(self, ctx: commands.Context) -> None:
        if ctx.guild is None:
            identifier = None
        else:
            identifier = ctx.guild.id

        await self.update(identifier)

    @staticmethod
    async def _interaction_respond(
        interaction: discord.Interaction,
        message: str
    ) -> None:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)

    def _runtime_directories_create(self) -> None:
        directories = [
            self.champion,
            self.logs,
            self.sound.joinpath('default'),
            self.sound.joinpath('member'),
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    async def dispose(self) -> None:
        if self.session is not None and not self.session.closed:
            await self.session.close()

        await databases.dispose()

    def extensions_discover(self) -> None:
        for path in self.root.iterdir():
            if not path.name.startswith('.') and path.joinpath('cog.py').is_file():
                name = path.name
                self.extension_names.append(name)

    async def extensions_load(self) -> None:
        for extension in self.extension_names:
            try:
                await self.load_extension(extension)
            except Exception:
                message = 'Failed to load extension: %s'
                log.exception(message, extension)

    async def update(self, identifier: int | str | None) -> bool:
        if identifier is None:
            identifier_text = None
        else:
            identifier_text = str(identifier)

        self.identifier.set(identifier_text)

        return identifier_text is not None and databases.guild(identifier_text) is not None

    async def setup_hook(self) -> None:
        self._runtime_directories_create()

        command_engine, command_session = engine_initialize(self.uri + 'command')

        command = DatabaseConfiguration(
            engine=command_engine,
            session=command_session,
            name='command',
        )

        databases.command_register(command)

        lol_engine, lol_session = engine_initialize(self.uri + 'lol')

        lol = DatabaseConfiguration(
            engine=lol_engine,
            session=lol_session,
            name='lol',
        )

        databases.lol_register(lol)

        for guild_identifier, name in configuration['guilds'].items():
            engine, session = engine_initialize(self.uri + name)

            database_configuration = DatabaseConfiguration(
                engine=engine,
                session=session,
                name=name,
            )

            databases.guild_register(guild_identifier, database_configuration)

        self.session = aiohttp.ClientSession()

        self.before_invoke(self._identifier_set)

        self.tree.error(self.on_app_command_error)

        self.extensions_discover()
        await self.extensions_load()

        self.purge.start()

    async def start(self) -> None:
        await super().start(self.token, reconnect=True)

    # Event Listeners

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """
        An event that is called when an error is raised while invoking
        an application command. This covers the app-command layer that
        on_command_error does not see: cooldowns, checks, transformers
        and pure slash commands.
        """

        match error:
            case app_commands.CommandOnCooldown():
                seconds = ceil(error.retry_after)

                message = (
                    f'This command is on cooldown. '
                    f'Please wait {seconds} seconds.'
                )

            case (
                app_commands.MissingPermissions() |
                app_commands.MissingRole() |
                app_commands.CheckFailure()
            ):
                message = 'You do not have permission to use this command.'

            case app_commands.TransformerError():
                message = 'That input could not be resolved.'

            case _:
                traceback.print_exception(type(error), error, error.__traceback__)

                command = interaction.command

                if command is None:
                    name = 'unknown'
                else:
                    name = command.qualified_name

                warning = f'{error.__class__.__name__} from {name}.'
                log.warning(warning)

                message = 'An unexpected error occurred.'

        await self._interaction_respond(interaction, message)

    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError
    ) -> None:
        """
        An event that is called when an error is raised while invoking
        a command.
        """

        match error:
            case commands.CommandOnCooldown():
                seconds = ceil(error.retry_after)

                message = (
                    f'This command is on cooldown. '
                    f'Please wait {seconds} seconds.'
                )

                await ctx.send(message)

            case commands.CommandNotFound():
                repository = CommandRepository(databases.command.session)
                rows = await repository.suggestions_get(ctx.invoked_with)

                if len(rows) == 0:
                    message = 'Command not found.'
                    await ctx.send(message)

                    return

                embed = embeds.suggestion_embed(rows, self.colour)
                await ctx.send(embed=embed)

            case GuildContextError():
                message = 'This command can only be used in a configured server.'
                await ctx.send(message)

            case commands.CheckFailure() | commands.MissingPermissions() | commands.MissingRole():
                message = 'You do not have permission to use this command.'
                await ctx.send(message)

            case commands.BadArgument() | commands.MissingRequiredArgument():
                return

            case _:
                traceback.print_exception(type(error), error, error.__traceback__)

                command = ctx.command

                if command is None:
                    name = 'unknown'
                else:
                    name = command.qualified_name

                message = f'{error.__class__.__name__} from {name}.'
                log.warning(message)

                if hasattr(error, 'original'):
                    log.warning(error.original)

    async def on_connect(self) -> None:
        """
        An event that is called when the client has successfully
        connected to Discord.
        """

        message = f'{self.bot_name} is connected.'
        log.info(message)

    async def on_message(self, message: discord.Message) -> None:
        """
        An event that is called every time a message is received,
        including Viking.
        """

        condition = (
            message.author.bot or
            message.content.startswith('**') or
            message.content.endswith('*')
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
            ['ID', self.bot_identifier],
            ['Name', self.bot_name],
            ['Python', f'{python.major}.{python.minor}.{python.micro}'],
            ['Discord.py', discord.__version__],
            ['Date', datetime.now(tz=UTC).strftime('%B %d, %Y at %I:%M %p')]
        ]

        display = tabulate(table, tablefmt='psql')
        print(display)

        message = f'{self.bot_name} is ready.'
        log.info(message)

    # Tasks

    @tasks.loop(time=time_of_day(hour=0, minute=0, tzinfo=UTC))
    async def purge(self) -> None:
        """
        A task that purges all messages from the spam channel at
        midnight.
        """

        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == PURGE_CHANNEL:
                    await channel.purge(limit=PURGE_MESSAGES_MAX)

    @purge.before_loop
    async def before_purge(self) -> None:
        await self.wait_until_ready()
