from __future__ import annotations

import discord
import logging

from discord.ext import commands
from model.role import DiscordRole
from typing import TYPE_CHECKING
from utilities.event import MemberEvent
from utilities.format import format_list
from utilities.member import DiscordMember, MemberInterface

if TYPE_CHECKING:
    from bot import Viking
    from discord import Guild, Member, User
    from discord.ext.commands import Context


log = logging.getLogger(__name__)


class Members(commands.Cog):
    def __init__(self, viking: Viking):
        self.viking = viking
        self.event = MemberEvent(self.viking)

    # Event Listeners

    @commands.Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        """
        An event that is called when a member joins the guild.
        """

        await self.viking.update(member.guild.id)

        removed = await self.event.is_member_removed(member.id)
        banned = await self.event.is_member_banned(member.id)

        if removed is None and banned is None:
            await self.event.member_create(member)
        else:
            await self.event.member_restore(member.id)
            await self.event.member_update(member)

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member) -> None:
        """
        An event that is called when a member changes their status, game,
        nickname or role.
        """

        await self.viking.update(before.guild.id)

        if before.nick != after.nick:
            if before.nick is None:
                await self.event.nickname_update(before, after)
            else:
                await self.event.nickname_append(before, after)

        if before.top_role.id != after.top_role.id or after.top_role < before.top_role:
            await self.event.member_role_update(before, after)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: Guild, member: Member) -> None:
        """
        An event that is called when a member is banned from the guild.
        """

        await self.viking.update(guild.id)
        await self.event.member_ban(member.id)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: Guild, member: Member) -> None:
        """
        An event that is called when a member is unbanned from the guild.
        """

        await self.viking.update(guild.id)
        await self.event.member_unban(member.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member) -> None:
        """
        An event that is called when a member is kicked or has left the
        guild.
        """

        await self.viking.update(member.guild.id)
        await self.event.member_remove(member.id)

    @commands.Cog.listener()
    async def on_user_update(self, before: User, after: User) -> None:
        """
        An event that is called when a member changes their avatar
        or username.
        """

        for guild in before.mutual_guilds:
            await self.viking.update(guild.id)

            if before.name != after.name:
                if before.name is None:
                    await self.event.name_update(before, after)
                else:
                    await self.event.name_append(before, after)

    # Commands

    @commands.command()
    async def about(self, ctx: Context, *, identifier: str) -> None:
        """
        *about <identifier>

        A command that displays an overview of a member.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        embed = discord.Embed(color=self.viking.color)

        row = dict(
            await self.viking.guild.member
            .query
            .execution_options(return_model=False)
            .where(self.viking.guild.member.discord_id == discord_id)
            .gino
            .first()
        )

        member = DiscordMember(row)

        row = dict(
            await self.viking.guild.role
            .select('name')
            .where(self.viking.guild.role.id == member.role_id)
            .gino
            .first()
        )

        role = DiscordRole(row)

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
    async def created(self, ctx: Context, *, identifier: str) -> None:
        """
        *created <identifier>

        A command that displays the date of when a member created
        their Discord account.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        row = dict(
            await self.viking.guild.member
            .select('display_name', 'created_at')
            .where(self.viking.guild.member.discord_id == discord_id)
            .gino
            .first()
        )

        member = DiscordMember(row)

        await ctx.send(
            f"{member.display_name} created their account "
            f"on {member.created}"
        )

    @commands.command()
    async def id(self, ctx: Context, *, identifier: str) -> None:
        """
        *id <identifier>

        A command that displays the name of a member from an ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        row = dict(
            await self.viking.guild.member
            .select('name')
            .where(self.viking.guild.member.discord_id == discord_id)
            .gino
            .first()
        )

        member = DiscordMember(row)
        await ctx.send(member.name)

    @commands.command()
    async def joined(self, ctx: Context, *, identifier: str) -> None:
        """
        *joined <identifier>

        A command that displays the date of when a member joined the
        guild.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        row = dict(
            await self.viking.guild.member
            .select('display_name', 'joined_at')
            .where(self.viking.guild.member.discord_id == discord_id)
            .gino
            .first()
        )

        member = DiscordMember(row)

        await ctx.send(
            f"{member.display_name} joined the server on "
            f"{member.joined}"
        )


async def setup(viking: Viking) -> None:
    members = Members(viking)
    await viking.add_cog(members)
