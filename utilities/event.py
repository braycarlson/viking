import discord
from datetime import datetime
from utilities.member import Member


class MemberEvent:
    def __init__(self, viking):
        self.viking = viking

    # Member Checks

    async def is_member_banned(self, member: int):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    SELECT
                    EXISTS(
                        SELECT name
                        FROM banned
                        WHERE discord_id = $1
                    )
                    """

            row = await connection.fetchval(query, member)
            return row

    async def is_member_removed(self, member: int):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    SELECT
                    EXISTS(
                        SELECT name
                        FROM removed
                        WHERE discord_id = $1
                    )
                    """

            row = await connection.fetchval(query, member)
            return row

    # Member Events

    async def member_create(self, member: discord.Member):
        async with self.viking.postgresql.acquire() as connection:
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
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """

            await connection.execute(
                query,
                member.id,
                member.name,
                member.discriminator,
                member.display_name,
                member.nick,
                self.viking.normal,
                member.bot,
                member.created_at,
                member.joined_at
            )

    async def member_ban(self, member: int):
        now = datetime.now()

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    INSERT INTO banned
                        SELECT * FROM members
                        WHERE discord_id = $1
                    """

            await connection.execute(query, member)

            query = """
                    UPDATE banned
                    SET deleted_at = $1
                    """

            await connection.execute(query, now)

    async def member_unban(self, member: int):
        now = datetime.now()

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    INSERT INTO removed
                        SELECT *
                        FROM banned
                        WHERE discord_id = $1
                    """

            await connection.execute(query, member)

            query = """
                    UPDATE removed
                    SET removed_at = $1
                    """

            await connection.execute(query, now)

    async def member_remove(self, member: int):
        now = datetime.now()

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    INSERT INTO removed
                        SELECT *
                        FROM members
                        WHERE discord_id = $1
                    """

            await connection.execute(query, member)

            query = """
                    UPDATE removed
                    SET removed_at = $1
                    """

            await connection.execute(query, now)

    async def member_restore(self, member: int):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    INSERT INTO members
                        SELECT *
                        FROM removed
                        WHERE discord_id = $1
                    """

            await connection.execute(query, member)

    async def member_delete(self, member: int, table='members'):
        async with self.viking.postgresql.acquire() as connection:
            query = f"""
                    DELETE FROM {table}
                    WHERE discord_id = $1
                    """

            await connection.execute(query, member)

    # Member Attributes

    # The 'update' functions will be called when a member updates their
    # name, discriminator or nickname for the first time in the server.
    # This will just update their attributes.

    async def name_update(self, before: discord.User, after: discord.User):
        now = datetime.now()

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    UPDATE members
                    SET (
                        name,
                        display_name,
                        updated_at
                    )
                    = ($1, $2, $3)
                    WHERE discord_id = $4
                    """

            await connection.execute(
                query,
                after.name,
                after.display_name,
                now,
                after.id
            )

    async def discriminator_update(self, before: discord.User, after: discord.User):
        now = datetime.now()

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    UPDATE members
                    SET (discriminator, updated_at)
                    = ($1, $2)
                    WHERE discord_id = $3
                    """

            await connection.execute(
                query,
                after.discriminator,
                now,
                after.id
            )

    async def nickname_update(self, before: discord.Member, after: discord.Member):
        now = datetime.now()

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    UPDATE members
                    SET (
                        nickname,
                        display_name,
                        updated_at
                    )
                    = ($1, $2, $3)
                    WHERE discord_id = $4
                    """

            await connection.execute(
                query,
                after.nick,
                after.display_name,
                now,
                after.id
            )

    async def member_role_update(self, before: discord.Member, after: discord.Member):
        now = datetime.now()

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    UPDATE members
                    SET (role_id, updated_at) = ($1, $2)
                    WHERE discord_id = $3
                    """

            await connection.execute(
                query,
                after.top_role.id,
                now,
                after.id
            )

    # The 'append' functions will be called when a member updates their
    # name, discriminator or nickname more than once in the server. This
    # will store their old attributes in an array.

    async def name_append(self, before: discord.User, after: discord.User):
        now = datetime.now()

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    UPDATE members
                    SET (
                        name,
                        previous_name,
                        display_name,
                        updated_at
                    )
                    = ($1, array_prepend($2, previous_name), $3, $4)
                    WHERE discord_id = $5
                    """

            await connection.execute(
                query,
                after.name,
                before.name,
                after.display_name,
                now,
                after.id
            )

    async def discriminator_append(self, before: discord.User, after: discord.User):
        now = datetime.now()

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    UPDATE members
                    SET (
                        discriminator,
                        previous_discriminator,
                        updated_at
                    )
                    = ($1, array_prepend($2, previous_discriminator), $3)
                    WHERE discord_id = $4
                    """

            await connection.execute(
                query,
                after.discriminator,
                before.discriminator,
                now,
                after.id
            )

    async def nickname_append(self, before: discord.Member, after: discord.Member):
        now = datetime.now()

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    UPDATE members
                    SET (
                        nickname,
                        previous_nickname,
                        display_name,
                        updated_at
                    )
                    = ($1, array_prepend($2, previous_nickname), $3, $4)
                    WHERE discord_id = $5
                    """

            await connection.execute(
                query,
                after.nick,
                before.nick,
                after.display_name,
                now,
                after.id
            )

    # These functions will handle the case where a member is kicked
    # from the server, and updates their information while they're
    # kicked. If the member rejoins the server, their database record
    # will be updated and/or appended to.

    async def get_old_record(self, member: int):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    SELECT name,
                           discriminator,
                           nickname,
                           removed_at,
                           deleted_at
                    FROM removed
                    WHERE discord_id = $1
                    """

            return await connection.fetch(
                query,
                member
            )

    async def old_name_update(self, member: discord.Member, name: str):
        if name != member.name:
            async with self.viking.postgresql.acquire() as connection:
                query = """
                        UPDATE members
                        SET previous_name = array_prepend($1, previous_name)
                        WHERE discord_id = $2
                        """

                await connection.execute(
                    query,
                    name,
                    member.id
                )

    async def old_discriminator_update(self, member: discord.Member, discriminator: str):
        if discriminator != member.discriminator:
            async with self.viking.postgresql.acquire() as connection:
                query = """
                        UPDATE members
                        SET previous_discriminator
                        = array_prepend($1, previous_discriminator)
                        WHERE discord_id = $2
                        """

                await connection.execute(
                    query,
                    discriminator,
                    member.id
                )

    async def old_nickname_update(self, member: discord.Member, nickname: str):
        if nickname != member.nick:
            async with self.viking.postgresql.acquire() as connection:
                query = """
                        UPDATE members
                        SET previous_nickname
                        = array_prepend($1, previous_nickname)
                        WHERE discord_id = $2
                        """

                await connection.execute(
                    query,
                    nickname,
                    member.id
                )

    async def member_update(self, member: discord.Member):
        now = datetime.now()
        rows = await self.get_old_record(member.id)

        for row in rows:
            old = Member(row)

        await self.old_name_update(member, old.name)
        await self.old_discriminator_update(member, old.discriminator)
        await self.old_nickname_update(member, old.nickname)

        async with self.viking.postgresql.acquire() as connection:
            query = """
                    UPDATE members
                    SET (
                        name,
                        discriminator,
                        display_name,
                        nickname,
                        role_id,
                        joined_at,
                        updated_at,
                        removed_at,
                        deleted_at
                    )
                    = ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    WHERE discord_id = $10
                    """

            await connection.execute(
                query,
                member.name,
                member.discriminator,
                member.display_name,
                member.nick,
                self.viking.normal,
                now,
                now,
                old.removed_at,
                old.deleted_at,
                member.id
            )


class RoleEvent:
    def __init__(self, viking):
        self.viking = viking

    async def role_create(self, role: discord.Role):
        async with self.viking.postgresql.acquire() as connection:
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

    async def role_add(self):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    SELECT discord_id
                    FROM members
                    WHERE role_id = 186994904365400064
                    """

            rows = await connection.fetch(query)

            for guild in self.viking.guilds:
                role = discord.utils.get(guild.roles, id=self.viking.normal)

            for row in rows:
                discord_id = row.get('discord_id')
                member = guild.get_member(discord_id)
                await member.add_roles(role)

    async def role_update(self, role: discord.Role):
        async with self.viking.postgresql.acquire() as connection:
            query = """
                    UPDATE roles
                    SET (
                        id,
                        name,
                        colour,
                        hoist,
                        position,
                        managed,
                        mentionable,
                        is_default,
                        created_at
                    ) = ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    WHERE id = $1
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

    async def role_delete(self, role_id: int):
        async with self.viking.postgresql.acquire() as connection:
            query = f"""
                    DELETE FROM roles
                    WHERE id = $1
                    """

            await connection.execute(query, role_id)

    async def role_replace(self, after: discord.Role):
        now = datetime.now()

        async with self.viking.postgresql.acquire() as connection:
            for guild in self.viking.guilds:
                for member in guild.members:
                    query = """
                            SELECT role_id
                            FROM members
                            WHERE discord_id = $1
                            """

                    row = await connection.fetchval(
                        query,
                        member.id
                    )

                    if row != member.top_role.id:
                        query = """
                                UPDATE members
                                SET (role_id, updated_at) = ($1, $2)
                                WHERE discord_id = $3
                                """

                        await connection.execute(
                            query,
                            after.id,
                            now,
                            member.id
                        )
