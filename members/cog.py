from __future__ import annotations

import discord

from typing_extensions import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from members import embeds
from members.autocomplete import member_autocomplete
from members.interface import identifier_get
from members.repository import MemberRepository
from members.service import MemberEvent
from roles.models import DiscordRole
from roles.repository import RoleRepository

if TYPE_CHECKING:
    from discord import Guild, Member, User
    from discord.ext.commands import Context

    from bot import Viking


ABOUT_MENU = 'About'


async def about_menu(interaction: discord.Interaction, member: discord.Member) -> None:
    viking = interaction.client

    if not await viking.update(interaction.guild_id):
        message = 'This command can only be used in a configured server.'
        await interaction.response.send_message(message, ephemeral=True)

        return

    await interaction.response.defer(ephemeral=True)

    session_maker = viking.guild.session

    record = await MemberRepository(session_maker).record_get(member.id)

    if record is None:
        message = 'Member not found.'
        await interaction.followup.send(message, ephemeral=True)

        return

    role_name = await RoleRepository(session_maker).name_get(record.role_identifier)
    role = DiscordRole(name=role_name)

    embed = embeds.about_embed(record, role, viking.colour)
    await interaction.followup.send(embed=embed, ephemeral=True)


class Members(commands.Cog):
    def __init__(self, viking: Viking) -> None:
        self.viking = viking
        self.event = MemberEvent(self.viking)

    @property
    def members(self) -> MemberRepository:
        return MemberRepository(self.viking.guild.session)

    @property
    def roles(self) -> RoleRepository:
        return RoleRepository(self.viking.guild.session)

    # Event Listeners

    @commands.Cog.listener()
    async def on_member_ban(self, guild: Guild, member: Member) -> None:
        if not await self.viking.update(guild.id):
            return

        await self.event.member_ban(member.id)

    @commands.Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        if not await self.viking.update(member.guild.id):
            return

        removed = await self.event.member_is_removed(member.id)
        banned = await self.event.member_is_banned(member.id)

        if not removed and not banned:
            await self.event.member_create(member)
        else:
            await self.event.member_restore(member.id)
            await self.event.member_update(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member) -> None:
        if not await self.viking.update(member.guild.id):
            return

        await self.event.member_remove(member.id)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: Guild, member: Member) -> None:
        if not await self.viking.update(guild.id):
            return

        await self.event.member_unban(member.id)

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member) -> None:
        if not await self.viking.update(before.guild.id):
            return

        if before.nick != after.nick:
            if before.nick is None:
                await self.event.nickname_update(after)
            else:
                await self.event.nickname_append(before, after)

        if before.top_role.id != after.top_role.id:
            await self.event.role_update(after)

    @commands.Cog.listener()
    async def on_user_update(self, before: User, after: User) -> None:
        if before.name == after.name:
            return

        for guild in before.mutual_guilds:
            if not await self.viking.update(guild.id):
                continue

            await self.event.name_append(before, after)

    # Commands

    @commands.hybrid_command(description='Display an overview of a member.')
    @app_commands.describe(identifier='The member by name, nickname or ID.')
    @app_commands.autocomplete(identifier=member_autocomplete)
    async def about(self, ctx: Context, *, identifier: str) -> None:
        """
        *about <identifier>

        A command that displays an overview of a member.
        """

        await ctx.typing()

        discord_id = await identifier_get(ctx, identifier)

        if discord_id is None:
            return

        member = await self.members.record_get(discord_id)

        if member is None:
            message = 'Member not found.'
            await ctx.send(message)

            return

        role_name = await self.roles.name_get(member.role_identifier)
        role = DiscordRole(name=role_name)

        embed = embeds.about_embed(member, role, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display when a member created their account.')
    @app_commands.describe(identifier='The member by name, nickname or ID.')
    @app_commands.autocomplete(identifier=member_autocomplete)
    async def created(self, ctx: Context, *, identifier: str) -> None:
        """
        *created <identifier>

        A command that displays the date of when a member created
        their Discord account.
        """

        await ctx.typing()

        discord_id = await identifier_get(ctx, identifier)

        if discord_id is None:
            return

        member = await self.members.created_get(discord_id)

        if member is None:
            message = 'Member not found.'
            await ctx.send(message)

            return

        message = f'{member.display_name} created their account on {member.created}'
        await ctx.send(message)

    @commands.hybrid_command(description='Display the name of a member from an ID.')
    @app_commands.describe(identifier='The member by name, nickname or ID.')
    @app_commands.autocomplete(identifier=member_autocomplete)
    async def id(self, ctx: Context, *, identifier: str) -> None:
        """
        *id <identifier>

        A command that displays the name of a member from an ID.
        """

        await ctx.typing()

        discord_id = await identifier_get(ctx, identifier)

        if discord_id is None:
            return

        name = await self.members.name_get(discord_id)

        if name is None:
            message = 'Member not found.'
            await ctx.send(message)

            return

        await ctx.send(name)

    @commands.hybrid_command(description='Display when a member joined the guild.')
    @app_commands.describe(identifier='The member by name, nickname or ID.')
    @app_commands.autocomplete(identifier=member_autocomplete)
    async def joined(self, ctx: Context, *, identifier: str) -> None:
        """
        *joined <identifier>

        A command that displays the date of when a member joined the
        guild.
        """

        await ctx.typing()

        discord_id = await identifier_get(ctx, identifier)

        if discord_id is None:
            return

        member = await self.members.joined_get(discord_id)

        if member is None:
            message = 'Member not found.'
            await ctx.send(message)

            return

        message = f'{member.display_name} joined the server on {member.joined}'
        await ctx.send(message)


async def setup(viking: Viking) -> None:
    members = Members(viking)
    await viking.add_cog(members)

    menu = app_commands.ContextMenu(name=ABOUT_MENU, callback=about_menu)
    viking.tree.add_command(menu)


async def teardown(viking: Viking) -> None:
    viking.tree.remove_command(ABOUT_MENU, type=discord.AppCommandType.user)
