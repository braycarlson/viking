import asyncio
import discord
from database.model import (
    database,
    ActiveMembers,
    BannedMembers,
    RemovedMembers
)


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


async def get_member_by_id(self, ctx, identifier, table='members'):
    """
    A function to get a member by ID from the database.
    """

    try:
        discord_id = int(identifier)
    except ValueError:
        name = identifier.lower()
        return await get_member_by_name(self, ctx, name, table)
    else:
        if table == 'members':
            table = ActiveMembers

        if table == 'banned_members':
            table = BannedMembers

        if table == 'removed_members':
            table = RemovedMembers

        row = (
            await table
            .select('discord_id')
            .where(table.discord_id == discord_id)
            .gino
            .scalar()
        )

        if row is None:
            raise MemberError

        return row


async def get_member_by_discriminator(self, ctx, member_name, member_discriminators, table):
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
        return (
            await ActiveMembers
            .select('discord_id')
            .where(
                (database.func.levenshtein(
                    database.func.lower(ActiveMembers.display_name),
                    member_name
                ) <= 3) &
                (ActiveMembers.discriminator == message.content) |

                (database.func.levenshtein(
                    database.func.lower(ActiveMembers.name),
                    member_name
                ) <= 3) &
                (ActiveMembers.discriminator == message.content) |

                (database.func.levenshtein(
                    database.func.lower(ActiveMembers.nickname),
                    member_name
                ) <= 3) &
                (ActiveMembers.discriminator == message.content)
            )
            .gino
            .scalar()
        )


async def show_identical_members(self, ctx, rows):
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
        row = dict(row)
        member = Member(row)

        embed.add_field(name='Account Name', value=member.name)
        embed.add_field(name='Discriminator', value=member.discriminator)
        embed.add_field(name='Nickname', value=member.nickname)

    embed.add_field(
        name='\u200B',
        value='Please enter the member\'s discriminator.'
    )
    await ctx.send(embed=embed)


async def get_member_by_name(self, ctx, member_name, table):
    """
    A function to get a member by account name or nickname from the
    database.
    """

    rows = (
        await ActiveMembers
        .select(
            'discord_id',
            'name',
            'discriminator',
            'nickname'
        )
        .where(
            (database.func.levenshtein(
                database.func.lower(ActiveMembers.display_name),
                member_name
            ) <= 3) |

            (database.func.levenshtein(
                database.func.lower(ActiveMembers.name),
                member_name
            ) <= 3) |

            (database.func.levenshtein(
                database.func.lower(ActiveMembers.nickname),
                member_name
            ) <= 3)
        )
        .limit(5)
        .gino
        .all()
    )

    if len(rows) == 0:
        raise MemberError

    if len(rows) == 1:
        for row in rows:
            row = dict(row)
            return row.get('discord_id')

    if len(rows) > 1:
        await show_identical_members(self, ctx, rows)

        member_discriminators = []

        for row in rows:
            row = dict(row)
            member_discriminators.append(
                row.get('discriminator')
            )

        return await get_member_by_discriminator(
            self,
            ctx,
            member_name,
            member_discriminators,
            table
        )
