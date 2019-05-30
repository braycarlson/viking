from discord.ext import commands


class Database(commands.Cog):
    def __init__(self, viking):
        self.viking = viking

    async def create_public_commands_table(self):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE TABLE IF NOT EXISTS public_commands(
                        id SERIAL PRIMARY KEY,
                        name TEXT,
                        aliases TEXT[] NULL
                    )
                    """

            await connection.execute(query)

    async def create_hidden_commands_table(self):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE TABLE IF NOT EXISTS hidden_commands(
                        id SERIAL PRIMARY KEY,
                        name TEXT,
                        aliases TEXT[] NULL
                    )
                    """

            await connection.execute(query)

    async def create_roles_table(self):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE TABLE IF NOT EXISTS roles(
                        id BIGINT PRIMARY KEY,
                        name TEXT,
                        colour VARCHAR,
                        hoist BOOLEAN,
                        position SMALLINT,
                        managed BOOLEAN,
                        mentionable BOOLEAN,
                        is_default BOOLEAN,
                        created_at TIMESTAMP
                    )
                    """

            await connection.execute(query)

    async def create_members_table(self):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE TABLE IF NOT EXISTS members(
                        discord_id BIGINT PRIMARY KEY,
                        name TEXT,
                        discriminator VARCHAR,
                        display_name TEXT,
                        nickname TEXT NULL,
                        role_id BIGINT REFERENCES roles (id),
                        bot BOOLEAN,
                        previous_name TEXT[] NULL,
                        previous_discriminator VARCHAR[] NULL,
                        previous_nickname TEXT[] NULL,
                        created_at TIMESTAMP NULL,
                        joined_at TIMESTAMP NULL,
                        updated_at TIMESTAMP NULL,
                        removed_at TIMESTAMP NULL,
                        deleted_at TIMESTAMP NULL
                    )
                    """

            await connection.execute(query)

    async def create_removed_table(self):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE TABLE IF NOT EXISTS removed(
                        LIKE members INCLUDING ALL
                    )
                    """

            await connection.execute(query)

    async def create_banned_table(self):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE TABLE IF NOT EXISTS banned(
                        LIKE members INCLUDING ALL
                    )
                    """

            await connection.execute(query)

    async def index_member_name(self):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE INDEX index_member_name
                    ON members (lower(name))
                    """

            await connection.execute(query)

    async def index_member_nickname(self):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE INDEX index_member_nickname
                    ON members (lower(nickname))
                    """

            await connection.execute(query)

    async def index_role_name(self):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE INDEX index_role_name
                    ON roles (lower(name))
                    """

            await connection.execute(query)

    async def index_public_commands_name(self):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE UNIQUE INDEX index_public_commands
                    ON public_commands (name)
                    """

            await connection.execute(query)

    async def index_hidden_commands_name(self):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    CREATE UNIQUE INDEX index_hidden_commands
                    ON hidden_commands (name)
                    """

            await connection.execute(query)

    async def insert_roles(self):
        async with self.viking.postgresql.acquire() as connection:
            for guild in self.viking.guilds:
                for role in guild.roles:

                    query = """
                            INSERT INTO roles(
                                id,
                                name,
                                colour,
                                hoist,
                                position,
                                managed,
                                mentionable,
                                is_default,
                                created_at
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                            """

                    await connection.execute(
                        query,
                        role.id,
                        role.name,
                        str(role.colour),
                        role.hoist,
                        role.position,
                        role.managed,
                        role.mentionable,
                        role.is_default(),
                        role.created_at,
                    )

    async def insert_public_commands(self):
        async with self.viking.postgresql.acquire() as connection:
            for viking_commands in self.viking.commands:
                if not viking_commands.hidden:
                    query = """
                            INSERT INTO public_commands (name)
                            VALUES ($1)
                            """

                    await connection.execute(query, viking_commands.name)

                    if viking_commands.aliases:
                        for alias in viking_commands.aliases:
                            query = """
                                    UPDATE public_commands
                                    SET aliases = array_prepend($1, aliases)
                                    WHERE name = $2
                                    """

                            await connection.execute(
                                query,
                                alias,
                                viking_commands.name
                            )

    async def insert_hidden_commands(self):
        async with self.viking.postgresql.acquire() as connection:
            for viking_commands in self.viking.commands:
                if viking_commands.hidden:
                    query = """
                            INSERT INTO hidden_commands (name)
                            VALUES ($1)
                            """

                    await connection.execute(query, viking_commands.name)

                    if viking_commands.aliases:
                        for alias in viking_commands.aliases:
                            query = """
                                    UPDATE hidden_commands
                                    SET aliases = array_prepend($1, aliases)
                                    WHERE name = $2
                                    """

                            await connection.execute(
                                query,
                                alias,
                                viking_commands.name
                            )

    async def insert_members(self):
        async with self.viking.postgresql.acquire() as connection:
            for guild in self.viking.guilds:
                for member in guild.members:
                    query = """
                            INSERT INTO members(
                                discord_id,
                                name,
                                discriminator,
                                display_name,
                                nickname,
                                role_id,
                                bot,
                                created_at,
                                joined_at
                            )
                            VALUES ($1, $2, $3, $4, $5,
                            $6, $7, $8, $9)
                            """

                    await connection.execute(
                        query,
                        member.id,
                        member.name,
                        member.discriminator,
                        member.display_name,
                        member.nick,
                        member.top_role.id,
                        member.bot,
                        member.created_at,
                        member.joined_at
                    )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def drop(self, ctx):
        """
        *drop <table>

        A command that drops all tables in the database.

        Note: This isn't great, but I am hoping to implement a database
        migration feature in the future.
        """

        await ctx.message.delete()

        async with self.viking.postgresql.acquire() as connection:
            async with connection.transaction():
                query = """
                        DROP TABLE IF EXISTS banned, hidden_commands, public_commands, removed, roles, subscriptions, members
                        """

                await connection.execute(query)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def run(self, ctx):
        """
        *run

        A command that executes the necessary queries to create the
        database.

        Note: This isn't great, but I am hoping to implement a database
        migration feature in the future.
        """

        await ctx.message.delete()

        # Create the tables
        await self.create_public_commands_table()
        await self.create_hidden_commands_table()
        await self.create_roles_table()
        await self.create_members_table()
        await self.create_removed_table()
        await self.create_banned_table()

        # Create the indexes
        await self.index_public_commands_name()
        await self.index_hidden_commands_name()
        await self.index_role_name()
        await self.index_member_name()
        await self.index_member_nickname()

        # Insert into the tables
        await self.insert_public_commands()
        await self.insert_hidden_commands()
        await self.insert_roles()
        await self.insert_members()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def truncate(self, ctx, table: str):
        """
        *truncate <table>

        A command that truncates a table in the database.

        Note: This isn't great, but I am hoping to implement a database
        migration feature in the future.
        """

        await ctx.message.delete()

        async with self.viking.postgresql.acquire() as connection:
            async with connection.transaction():
                query = f"""
                        TRUNCATE {table} RESTART IDENTITY
                        """
                await connection.execute(query)


def setup(viking):
    viking.add_cog(Database(viking))
