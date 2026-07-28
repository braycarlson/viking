from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from discord.ext import commands

from audio.repository import SoundRepository
from core.db.command import CommandRepository
from core.db.engine import CommandBase, GuildBase, LolBase
from core.db.registry import databases
from members.repository import MemberRepository
from roles.repository import RoleRepository

if TYPE_CHECKING:
    from collections.abc import Iterable

    from discord import Guild
    from discord.ext.commands import Context
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    from bot import Viking


class Migration(commands.Cog):
    def __init__(self, viking: Viking) -> None:
        self.viking = viking

    @property
    def repository(self) -> CommandRepository:
        return CommandRepository(databases.command.session)

    @staticmethod
    def _entries_build(
        selected: Iterable[commands.Command]
    ) -> list[tuple[str, list[str] | None]]:
        entries = []

        for command in selected:
            if command.aliases:
                aliases = list(command.aliases)
            else:
                aliases = None

            entry = (command.name, aliases)
            entries.append(entry)

        return entries

    async def _public_reconcile(self) -> None:
        rows = await self.repository.public_names_get()
        database_commands = set(rows)

        viking_commands = {
            command.name
            for command in self.viking.commands
            if not command.hidden
        }

        in_viking = [
            name
            for name in viking_commands
            if name not in database_commands
        ]

        in_database = [
            name
            for name in database_commands
            if name not in viking_commands
        ]

        if in_viking:
            selected = [
                command
                for command in self.viking.commands
                if not command.hidden and command.name in in_viking
            ]

            entries = self._entries_build(selected)

            await self.repository.public_create(entries)

        if in_database:
            await self.repository.public_delete(in_database)

    async def hidden_insert(self) -> None:
        selected = [
            command
            for command in self.viking.commands
            if command.hidden
        ]

        entries = self._entries_build(selected)

        await self.repository.hidden_create(entries)

    async def member_insert(
        self,
        session_maker: async_sessionmaker[AsyncSession],
        guild: Guild
    ) -> None:
        repository = MemberRepository(session_maker)
        await repository.create_many(list(guild.members))

    async def public_insert(self) -> None:
        selected = [
            command
            for command in self.viking.commands
            if not command.hidden
        ]

        entries = self._entries_build(selected)

        await self.repository.public_create(entries)

    async def role_insert(
        self,
        session_maker: async_sessionmaker[AsyncSession],
        guild: Guild
    ) -> None:
        repository = RoleRepository(session_maker)
        await repository.create_many(list(guild.roles))

    async def sound_insert(
        self,
        session_maker: async_sessionmaker[AsyncSession]
    ) -> None:
        directory = self.viking.sound.joinpath('member')

        if not directory.is_dir():
            return

        names = [sound.stem for sound in directory.iterdir()]

        repository = SoundRepository(session_maker)
        await repository.create_many(names, self.viking.bot_identifier)

    # Commands

    @commands.command(hidden=True)
    @commands.is_owner()
    async def create(self, ctx: Context) -> None:
        """
        *create

        A command that executes the necessary queries to create the
        database(s).
        """

        await ctx.message.delete()

        for configuration in databases.guilds():
            async with configuration.engine.begin() as connection:
                await connection.run_sync(GuildBase.metadata.create_all)

        async with databases.command.engine.begin() as connection:
            await connection.run_sync(CommandBase.metadata.create_all)

        async with databases.lol.engine.begin() as connection:
            await connection.run_sync(LolBase.metadata.create_all)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def drop(self, ctx: Context) -> None:
        """
        *drop

        A command that drops all tables in the database(s).
        """

        await ctx.message.delete()

        for configuration in databases.guilds():
            async with configuration.engine.begin() as connection:
                await connection.run_sync(GuildBase.metadata.drop_all)

        async with databases.command.engine.begin() as connection:
            await connection.run_sync(CommandBase.metadata.drop_all)

        async with databases.lol.engine.begin() as connection:
            await connection.run_sync(LolBase.metadata.drop_all)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def run(self, ctx: Context) -> None:
        """
        *run

        A command that executes the necessary queries to insert
        information into the database.
        """

        await ctx.message.delete()

        for guild in self.viking.guilds:
            configuration = databases.guild(str(guild.id))

            if configuration is not None:
                await self.role_insert(configuration.session, guild)
                await self.member_insert(configuration.session, guild)
                await self.sound_insert(configuration.session)

        await self.public_insert()
        await self.hidden_insert()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def update(self, ctx: Context) -> None:
        """
        *update

        A command that executes the necessary queries to update the
        database(s).
        """

        await ctx.message.delete()
        await self._public_reconcile()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def update_public(self, ctx: Context) -> None:
        """
        *update_public

        A command that reconciles the public command registry with the
        commands that are currently loaded, without deleting the
        invoking message.
        """

        await self._public_reconcile()

        message = 'The public command registry was reconciled.'
        await ctx.send(message)


async def setup(viking: Viking) -> None:
    migration = Migration(viking)
    await viking.add_cog(migration)
