import asyncpg
from discord.ext import commands
from utilities.redis import Redis


class PostgreSQL:
    def __init__(self, viking):
        self.viking = viking
        self.redis = Redis(viking)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def create_commands(self, ctx):
        """*create_commands

        A command that will create the commands table.
        """

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE TABLE IF NOT EXISTS commands(
                    id serial PRIMARY KEY,
                    name text
                    )
                    """

            await connection.execute(query)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def create_members(self, ctx):
        """*create_members

        A command that will create the members table.
        """

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE TABLE IF NOT EXISTS members(
                    id serial PRIMARY KEY,
                    name text,
                    discriminator varchar,
                    nickname text,
                    bot boolean,
                    discord_id bigint
                    )
                    """

            await connection.execute(query)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def index_commands(self, ctx):
        """*index_commands

        A command that will create a unique index on the commands table.
        """

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE UNIQUE INDEX index_commands on commands (name);
                    """

            await connection.execute(query)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def index_members(self, ctx):
        """*index_commands

        A command that will create a unique index on the members table.
        """

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE UNIQUE INDEX index_members on members (discord_id);
                    """

            await connection.execute(query)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def insert_commands(self, ctx):
        """*insert_commands

        A command that will insert every command into the database.
        """

        async with self.viking.postgresql.acquire() as connection:
            for viking_commands in self.viking.commands:
                query = """
                        INSERT INTO commands (name)
                        VALUES ($1)
                        """

                await connection.execute(query, viking_commands.name)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def insert_members(self, ctx):
        """*insert_members

        A command that will insert every member into the database.
        """

        async with self.viking.postgresql.acquire() as connection:
            for members in ctx.guild.members:
                query = """
                        INSERT INTO members (name, discriminator, nickname, bot, discord_id)
                        VALUES ($1, $2, $3, $4, $5)
                        """

                await connection.execute(query, members.name, members.discriminator, members.nick, members.bot, members.id)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def truncate(self, ctx, table: str):
        """*truncate <table>

        A command that will truncate a table in the database.
        """

        async with self.viking.postgresql.acquire() as connection:
            try:
                async with connection.transaction():
                    await connection.execute(f"TRUNCATE {table} RESTART IDENTITY;")
                await ctx.send(f"`{table}` was truncated.")
            except asyncpg.exceptions.UndefinedTableError:
                await ctx.send(f"`{table}` does not exist.")


def setup(viking):
    viking.add_cog(PostgreSQL(viking))
