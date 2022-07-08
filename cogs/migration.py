import database.engine

from database.command import Hidden, Public
from database.nac import Member, Role, Sound
from database.viking import Member, Role, Sound
from datetime import datetime
from discord.ext import commands
from sqlalchemy import func


class Migration(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.bot_id = viking.bot_id
        self.root = viking.root
        self.sound = viking.sound

    async def insert_member(self, model, guild):
        for member in guild.members:
            await model.create(
                discord_id=member.id,
                name=member.name,
                discriminator=member.discriminator,
                display_name=member.display_name,
                nickname=member.nick,
                role_id=member.top_role.id,
                bot=member.bot,
                created_at=member.created_at,
                joined_at=member.joined_at
            )

    async def insert_role(self, model, guild):
        for role in guild.roles:
            await model.create(
                id=role.id,
                name=role.name,
                colour=str(role.colour),
                hoist=role.hoist,
                position=role.position,
                managed=role.managed,
                mentionable=role.mentionable,
                is_default=role.is_default(),
                created_at=role.created_at
            )

    async def insert_sound(self, model):
        directory = self.sound.joinpath('member')
        sounds = [path for path in directory.iterdir()]
        date = datetime.now()

        for sound in sounds:
            await model.create(
                name=sound.stem,
                created_by=self.bot_id,
                created_at=date
            )

    async def insert_public(self):
        for viking_commands in self.viking.commands:
            if not viking_commands.hidden:
                await Public.create(name=viking_commands.name)

                if viking_commands.aliases:
                    for alias in viking_commands.aliases:
                        (
                            await Public
                            .update
                            .values(
                                aliases=func.array_prepend(
                                    alias,
                                    Public.aliases
                                )
                            )
                            .where(Public.name == viking_commands.name)
                            .gino
                            .status()
                        )

    async def insert_hidden(self):
        for viking_commands in self.viking.commands:
            if viking_commands.hidden:
                await Hidden.create(name=viking_commands.name)

                if viking_commands.aliases:
                    for alias in viking_commands.aliases:
                        (
                            await Hidden
                            .update
                            .values(
                                aliases=func.array_prepend(
                                    alias,
                                    Hidden.aliases
                                )
                            )
                            .where(Hidden.name == viking_commands.name)
                            .gino
                            .status()
                        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def update_public(self, ctx):
        query = await Public.select('name').gino.all()

        database_commands = set(
            dict(commands).get('name')
            for commands in query
        )

        viking_commands = set(
            commands.name
            for commands in self.viking.commands
            if not commands.hidden
        )

        in_viking = [
            command
            for command in viking_commands
            if command not in database_commands
        ]

        in_database = [
            command
            for command in database_commands
            if command not in viking_commands
        ]

        # If a command exists in Viking, and not in the database; update the database
        if in_viking:
            for command in self.viking.commands:
                if not command.hidden:
                    if command.name in in_viking:
                        await Public.create(name=command.name)

                        if command.aliases:
                            for alias in command.aliases:
                                (
                                    await Public
                                    .update
                                    .values(
                                        aliases=func.array_prepend(
                                            alias,
                                            Public.aliases
                                        )
                                    )
                                    .where(Public.name == command.name)
                                    .gino
                                    .status()
                                )

        # If a command exists in the database, and not in Viking; delete from database
        if in_database:
            for command in in_database:
                (
                    await Public
                    .delete
                    .where(Public.name == command)
                    .gino
                    .status()
                )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def drop(self, ctx):
        """
        *drop <table>

        A command that drops all tables in the database(s).
        """

        await ctx.message.delete()

        guild = database.engine.Guild()

        for engine in guild.generate('engine'):
            await engine.gino.drop_all()

        await database.engine.command.gino.drop_all()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def update(self, ctx):
        """
        *update

        A command that executes the necessary queries to update the
        database(s).
        """

        await ctx.message.delete()
        await self.update_public_commands()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def create(self, ctx):
        """
        *create

        A command that executes the necessary queries to create the
        database(s).
        """

        await ctx.message.delete()

        guild = database.engine.Guild()

        for engine in guild.generate('engine'):
            await engine.gino.create_all()

        await database.engine.command.gino.create_all()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def run(self, ctx):
        """
        *run

        A command that executes the necessary queries to insert
        information into the database.
        """

        await ctx.message.delete()

        guilds = database.engine.Guild()

        for guild in self.viking.guilds:
            gid = str(guild.id)
            model = guilds.get(gid)

            await self.insert_role(model.role, guild)
            await self.insert_member(model.member, guild)
            await self.insert_sound(model.sound)

        await self.insert_public()
        await self.insert_hidden()


async def setup(viking):
    migration = Migration(viking)
    await viking.add_cog(migration)
