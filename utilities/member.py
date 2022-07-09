import asyncio
import discord

from model.member import DiscordMember, DiscordMemberError
from sqlalchemy import func


class MemberInterface:
    def __init__(self, context, identifier):
        self.context = context
        self.identifier = identifier
        self.viking = context.bot

    async def get(self):
        discord_id = None

        try:
            discord_id = await self.from_id()
        except DiscordMemberError:
            message = 'No member found.'
            await self.context.send(message)
        except asyncio.TimeoutError:
            message = 'You have run out of time. Please try again.'
            await self.context.send(message)
        finally:
            return discord_id

    async def from_id(self):
        """
        A function to get a member by ID from the database.
        """

        try:
            discord_id = int(self.identifier)
        except ValueError:
            name = self.identifier.lower()
            return await self.from_name(name)
        else:
            row = (
                await self.viking.guild.member
                .select('discord_id')
                .where(self.viking.guild.member.discord_id == discord_id)
                .gino
                .scalar()
            )

            if row is None:
                raise DiscordMemberError

            return row

    async def from_name(self, name):
        """
        A function to get a member by account name or nickname from the
        database.
        """

        model = self.viking.guild.member

        condition = (
            (func.levenshtein(func.lower(model.display_name), name) <= 3) |
            (func.levenshtein(func.lower(model.name), name) <= 3) |
            (func.levenshtein(func.lower(model.nickname), name) <= 3)
        )

        rows = (
            await model
            .select(
                'discord_id',
                'display_name',
                'name',
                'discriminator',
                'nickname'
            )
            .where(condition)
            .limit(5)
            .gino
            .all()
        )

        length = len(rows)

        match length:
            case 0:
                raise DiscordMemberError

            case 1:
                for row in rows:
                    return dict(row).get('discord_id')

            case _:
                target = []

                for row in rows:
                    display_name = dict(row).get('display_name').lower()

                    if name == display_name.lower():
                        target.append(row)

                if len(target) == 1:
                    for member in target:
                        return dict(member).get('discord_id')

                await self.display_identical(self.context, rows)

                discriminators = [
                    dict(row).get('discriminator')
                    for row in rows
                ]

                return await self.from_discriminator(
                    name,
                    discriminators
                )

    async def from_discriminator(self, name, discriminator):
        """
        A function to get a member by discriminator to discern between
        members with identical account names or nicknames.
        """

        def check(message):
            condition = (
                message.author == self.context.author and
                message.channel == self.context.channel
            )

            if (condition):
                if message.content in discriminator:
                    return True

                raise DiscordMemberError

        try:
            message = await self.viking.wait_for(
                'message',
                check=check,
                timeout=15
            )
        except asyncio.TimeoutError:
            raise
        else:
            model = self.viking.guild.member

            condition = (
                (func.levenshtein(func.lower(model.display_name), name) <= 3) &
                (model.discriminator == message.content) |

                (func.levenshtein(func.lower(model.name), name) <= 3) &
                (model.discriminator == message.content) |

                (func.levenshtein(func.lower(model.nickname), name) <= 3) &
                (model.discriminator == message.content)
            )

            return (
                await model
                .select('discord_id')
                .where(condition)
                .gino
                .scalar()
            )

    async def display_identical(self, ctx, rows):
        """
        A function that will output each member with an identical account
        name or nickname.
        """

        length = len(rows)

        color = discord.Colour.purple()
        title = f"There are {length} members with identical information."

        embed = discord.Embed(color=color, title=title)

        for row in rows:
            row = dict(row)
            member = DiscordMember(row)

            embed.add_field(name='Account Name', value=member.name)
            embed.add_field(name='Discriminator', value=member.discriminator)
            embed.add_field(name='Nickname', value=member.nickname)

        embed.add_field(
            name='\u200B',
            value='Please enter the member\'s discriminator.'
        )

        await ctx.send(embed=embed)
