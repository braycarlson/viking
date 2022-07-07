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
        self.root = viking.root

    async def insert_roles(self, guild):
        for role in guild.roles:
            await self.viking.guild.role.create(
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

    async def insert_public_commands(self):
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

    async def insert_hidden_commands(self):
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

    async def insert_members(self, guild):
        for member in guild.members:
            await self.viking.guild.member.create(
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

    async def insert_member_sounds(self):
        directory = self.root.joinpath('sound/member')
        sounds = [path for path in directory.iterdir()]
        date = datetime.now()

        for sound in sounds:
            await self.viking.guild.sound.create(
                name=sound.stem,
                created_by=283002620023406593,
                created_at=date
            )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def update_public_commands(self, ctx):
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

        await database.engine.command.gino.drop_all()
        await database.engine.nac.gino.drop_all()
        await database.engine.viking.gino.drop_all()

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

        await database.engine.command.gino.create_all()
        await database.engine.nac.gino.create_all()
        await database.engine.viking.gino.create_all()

        await self.insert_public_commands()
        await self.insert_hidden_commands()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def run(self, ctx):
        """
        *run

        A command that executes the necessary queries to create the
        database.
        """

        await ctx.message.delete()

        await self.insert_roles(ctx.guild)
        await self.insert_members(ctx.guild)
        await self.insert_member_sounds()


async def setup(viking):
    migration = Migration(viking)
    await viking.add_cog(migration)
