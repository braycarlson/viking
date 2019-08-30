import discord
import logging
from asyncio import TimeoutError
from discord.ext import commands
from utilities.event import MemberEvent
from utilities.format import format_list
from utilities.member import Member, MemberError, get_member_by_id
from utilities.role import Role

log = logging.getLogger(__name__)


class Members(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.event = MemberEvent(self.viking)
        self.session = viking.session

    # Event Listeners

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        An event that is called when a member joins the guild.
        """

        for guild in self.viking.guilds:
            role = discord.utils.get(guild.roles, id=self.viking.normal)

            try:
                await member.add_roles(role)
            except discord.HTTPException:
                log.info(f"{member.name} could not be assigned the Normal role.")
            else:
                log.info(f"{member.name} was assigned the Normal role.")

        removed = await self.event.is_member_removed(member.id)

        if removed:
            await self.event.member_restore(member.id)
            await self.event.member_update(member)
            await self.event.member_delete(member.id, table='removed')
        else:
            await self.event.member_create(member)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        An event that is called when a member changes their status, game,
        nickname or role.
        """

        if before.nick != after.nick:
            if before.nick is None:
                await self.event.nickname_update(before, after)
            else:
                await self.event.nickname_append(before, after)

        if before.top_role.id != after.top_role.id or after.top_role < before.top_role:
            await self.event.member_role_update(before, after)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, member: discord.Member):
        """
        An event that is called when a member is banned from the guild.
        """

        await self.event.member_ban(member.id)
        await self.event.member_delete(member.id)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, member: discord.Member):
        """
        An event that is called when a member is unbanned from the guild.
        """

        await self.event.member_unban(member.id)
        await self.event.member_delete(member.id, table='banned')

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """
        An event that is called when a member is kicked or has left the
        guild.
        """

        await self.event.member_remove(member.id)
        await self.event.member_delete(member.id)

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        """
        An event that is called when a member changes their avatar,
        username or discriminator.
        """

        if before.name != after.name:
            if before.name is None:
                await self.event.name_update(before, after)
            else:
                await self.event.name_append(before, after)

        if before.discriminator != after.discriminator:
            if before.discriminator is None:
                await self.event.discriminator_update(before, after)
            else:
                await self.event.discriminator_append(before, after)

    # Commands

    @commands.command()
    async def about(self, ctx, *, identifier: str):
        """
        *about <identifier>

        A command that displays an overview of a member.
        """

        try:
            member_id = await get_member_by_id(self, ctx, identifier)
        except MemberError:
            await ctx.send('No member found.')
        except TimeoutError:
            await ctx.send('You have run out of time. Please try again.')
        else:
            embed = discord.Embed(color=self.viking.color)

            async with self.viking.postgresql.acquire() as connection:
                query = """
                        SELECT *
                        FROM members
                        WHERE discord_id = $1
                        """

                rows = await connection.fetch(query, member_id)

                for row in rows:
                    member = Member(row)

                query = """
                        SELECT name
                        FROM roles
                        WHERE id = $1
                        """

                rows = await connection.fetch(query, member.role_id)

                for row in rows:
                    role = Role(row)

                embed.add_field(
                    inline=False,
                    name='Discord ID',
                    value=member.id
                )
                embed.add_field(
                    inline=False,
                    name='Name',
                    value=member.name
                )
                embed.add_field(
                    inline=False,
                    name='Discriminator',
                    value=member.discriminator
                )

                if member.nickname is not None:
                    embed.add_field(
                        inline=False,
                        name='Nickname',
                        value=member.nickname
                    )

                embed.add_field(
                    inline=False,
                    name='Role',
                    value=role.name
                )
                embed.add_field(
                    inline=False,
                    name='Created At',
                    value=member.created
                )
                embed.add_field(
                    inline=False,
                    name='Joined At',
                    value=member.joined
                )

                if member.updated_at is not None:
                    embed.add_field(
                        inline=False,
                        name='Updated At',
                        value=member.updated
                    )

                if member.previous_name is not None:
                    previous_name = format_list(
                        member.previous_name,
                        symbol='bullet',
                        sort=False
                    )
                    embed.add_field(
                        inline=False,
                        name='Previous Names',
                        value=previous_name
                    )

                if member.previous_discriminator is not None:
                    previous_discriminator = format_list(
                        member.previous_discriminator,
                        symbol='bullet',
                        sort=False
                    )
                    embed.add_field(
                        inline=False,
                        name='Previous Discriminators',
                        value=previous_discriminator
                    )

                if member.previous_nickname is not None:
                    previous_nickname = format_list(
                        member.previous_nickname,
                        symbol='bullet',
                        sort=False
                    )
                    embed.add_field(
                        inline=False,
                        name='Previous Nicknames',
                        value=previous_nickname
                    )

                await ctx.send(embed=embed)

    @commands.command()
    async def created(self, ctx, *, identifier: str):
        """
        *created <identifier>

        A command that displays the date of when a member created
        their Discord account.
        """

        try:
            member_id = await get_member_by_id(self, ctx, identifier)
        except MemberError:
            await ctx.send('No member found.')
        except TimeoutError:
            await ctx.send('You have run out of time. Please try again.')
        else:
            async with self.viking.postgresql.acquire() as connection:
                query = """
                        SELECT display_name, created_at
                        FROM members
                        WHERE discord_id = $1
                        """

                rows = await connection.fetch(query, member_id)

                for row in rows:
                    member = Member(row)

                await ctx.send(
                    f"{member.display_name} created their account "
                    f"on {member.created}"
                )

    @commands.command()
    async def id(self, ctx, *, identifier: str):
        """
        *id <identifier>

        A command that displays the name and discriminator of a
        member from an ID.
        """

        try:
            member_id = await get_member_by_id(self, ctx, identifier)
        except MemberError:
            await ctx.send('No member found.')
        except TimeoutError:
            await ctx.send('You have run out of time. Please try again.')
        else:
            async with self.viking.postgresql.acquire() as connection:
                query = """
                        SELECT name, discriminator
                        FROM members
                        WHERE discord_id = $1
                        """

                rows = await connection.fetch(query, member_id)

                for row in rows:
                    member = Member(row)

                await ctx.send(f"{member.name}#{member.discriminator}")

    @commands.command()
    async def joined(self, ctx, *, identifier: str):
        """
        *joined <identifier>

        A command that displays the date of when a member joined the
        guild.
        """

        try:
            member_id = await get_member_by_id(self, ctx, identifier)
        except MemberError:
            await ctx.send('No member found.')
        except TimeoutError:
            await ctx.send('You have run out of time. Please try again.')
        else:
            async with self.viking.postgresql.acquire() as connection:
                query = """
                        SELECT display_name, joined_at
                        FROM members
                        WHERE discord_id = $1
                        """

                rows = await connection.fetch(query, member_id)

                for row in rows:
                    member = Member(row)

                await ctx.send(
                    f"{member.display_name} joined the server on "
                    f"{member.joined}"
                )


def setup(viking):
    viking.add_cog(Members(viking))
