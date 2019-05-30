import asyncio
import asyncpg
import discord
from typing import List


class MemberError(Exception):
    """
    A MemberError is raised when a member is not found in the database
    from user input. This can include by an ID, account name, nickname
    or discriminator.
    """

    pass


class Member:
    def __init__(self, data):
        self.id = data.get('discord_id')
        self.name = data.get('name')
        self.discriminator = data.get('discriminator')
        self.display_name = data.get('display_name')
        self.nickname = data.get('nickname')
        self.role_id = data.get('role_id')
        self.bot = data.get('bot')
        self.previous_name = data.get('previous_name')
        self.previous_discriminator = data.get('previous_discriminator')
        self.previous_nickname = data.get('previous_nickname')
        self.created_at = data.get('created_at')
        self.joined_at = data.get('joined_at')
        self.updated_at = data.get('updated_at')
        self.removed_at = data.get('removed_at')
        self.deleted_at = data.get('deleted_at')

    @property
    def created(self):
        return self.created_at.strftime('%B %d, %Y')

    @property
    def joined(self):
        return self.joined_at.strftime('%B %d, %Y')

    @property
    def updated(self):
        return self.updated_at.strftime('%B %d, %Y')

    @property
    def removed(self):
        return self.removed_at.strftime('%B %d, %Y')

    @property
    def deleted(self):
        return self.deleted_at.strftime('%B %d, %Y')


async def get_member_by_id(self, ctx, identifier: str, table='members'):
    """
    A function to get a member by ID from the database.
    """

    try:
        discord_id = int(identifier)
    except ValueError:
        name = identifier.lower()
        return await get_member_by_name(self, ctx, name, table)
    else:
        async with self.viking.postgresql.acquire() as connection:
            query = f"""
                    SELECT discord_id
                    FROM {table}
                    WHERE discord_id = $1
                    """

            row = await connection.fetchval(query, discord_id)

            if row is None:
                raise MemberError

            return row


async def get_member_by_discriminator(self, ctx, member_name: str, member_discriminators: List[str], table: str):
    """
    A function to get a member by discriminator to discern between
    members with identical account names or nicknames.
    """

    def check(message):
        if (message.author == ctx.author and
                message.channel == ctx.channel):

            if message.content in member_discriminators:
                return True

            raise MemberError

    try:
        message = await self.viking.wait_for(
            'message',
            check=check,
            timeout=15
        )
    except asyncio.TimeoutError:
        raise
    else:
        async with self.viking.postgresql.acquire() as connection:
            query = f"""
                    SELECT discord_id
                    FROM {table}
                    WHERE lower(name) = $1 AND discriminator = $2
                    OR lower(nickname) = $1 AND discriminator = $2
                    """

            return await connection.fetchval(
                query,
                member_name,
                message.content
            )


async def show_identical_members(self, ctx, rows: List[asyncpg.Record]):
    """
    A function that will output each member with an identical account
    name or nickname.
    """

    embed = discord.Embed(
        color=discord.Colour.purple(),
        title=f"There are {len(rows)} members "
              "with an identical account name or nickname."
    )

    for row in rows:
        member = Member(row)

        embed.add_field(name='Account Name', value=member.name)
        embed.add_field(name='Discriminator', value=member.discriminator)
        embed.add_field(name='Nickname', value=member.nickname)

    embed.add_field(
        name='\u200B',
        value='Please enter the member\'s discriminator.'
    )
    await ctx.send(embed=embed)


async def get_member_by_name(self, ctx, member_name: str, table: str):
    """
    A function to get a member by account name or nickname from the
    database.
    """

    async with self.viking.postgresql.acquire() as connection:
        query = f"""
                SELECT discord_id,
                       name,
                       discriminator,
                       nickname
                FROM {table}
                WHERE lower(name) = $1
                OR lower(nickname) = $1
                """

        rows = await connection.fetch(query, member_name)

        if len(rows) == 0:
            raise MemberError

        if len(rows) == 1:
            return await connection.fetchval(query, member_name)

        if len(rows) > 1:
            await show_identical_members(self, ctx, rows)
            member_discriminators = [row.get('discriminator') for row in rows]
            return await get_member_by_discriminator(
                self,
                ctx,
                member_name,
                member_discriminators,
                table
            )
