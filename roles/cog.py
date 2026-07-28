from __future__ import annotations

import logging

import discord

from typing_extensions import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from members.interface import member_get
from roles.autocomplete import role_autocomplete
from roles.layout import RoleCard
from roles.models import DiscordRoleError
from roles.repository import RoleRepository
from roles.service import RoleEvent
from roles.views import RolePanelBuilderView, RoleToggleButton

if TYPE_CHECKING:
    from discord import Role as MemberRole
    from discord.ext.commands import Context

    from bot import Viking


log = logging.getLogger(__name__)


class Roles(commands.Cog):
    def __init__(self, viking: Viking) -> None:
        self.viking = viking
        self.event = RoleEvent(self.viking)

    @property
    def roles(self) -> RoleRepository:
        return RoleRepository(self.viking.guild.session)

    # Event Listeners

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: MemberRole) -> None:
        if not await self.viking.update(role.guild.id):
            return

        await self.event.role_create(role)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: MemberRole) -> None:
        if not await self.viking.update(role.guild.id):
            return

        await self.event.role_delete(role.id)

    @commands.Cog.listener()
    async def on_guild_role_update(
        self,
        before: MemberRole,
        after: MemberRole
    ) -> None:
        if not await self.viking.update(before.guild.id):
            return

        await self.event.role_update(after)

        if before < after:
            await self.event.role_replace(after.guild)

    # Commands

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def addrole(self, ctx: Context, name: str, *, identifier: str) -> None:
        """
        *addrole <role> <identifier>

        A command that adds a role to a member by name, nickname or ID.
        """

        member = await member_get(ctx, identifier)

        if member is None:
            return

        role = discord.utils.get(ctx.guild.roles, name=name)

        if role is None:
            message = f'Role "{name}" not found.'
            await ctx.send(message)

            return

        try:
            await member.add_roles(role)
        except discord.HTTPException:
            message = f'{member} could not be assigned the {role} role.'
            await ctx.send(message)
        else:
            message = '%s assigned the role %s to %s.'
            log.info(message, ctx.author, role, member)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def createrole(self, ctx: Context, *, name: str) -> None:
        """
        *createrole <role>

        A command that creates a role with no permissions.
        """

        if await self.roles.name_exists(name):
            message = 'A role with that name already exists.'
            await ctx.send(message)

            return

        try:
            permissions = discord.Permissions.none()
            await ctx.guild.create_role(name=name, permissions=permissions)
        except discord.HTTPException:
            message = f'{name} could not be created.'
            await ctx.send(message)
        else:
            message = '%s created the role %s.'
            log.info(message, ctx.author, name)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def deleterole(self, ctx: Context, *, name: str) -> None:
        """
        *deleterole <role>

        A command that deletes a role.
        """

        if not await self.roles.name_exists(name):
            message = 'No role found.'
            await ctx.send(message)

            return

        role = discord.utils.get(ctx.guild.roles, name=name)

        if role is None:
            message = 'No role found.'
            await ctx.send(message)

            return

        try:
            await role.delete()
        except discord.HTTPException:
            message = f'{name} could not be deleted.'
            await ctx.send(message)
        else:
            message = '%s deleted the role %s.'
            log.info(message, ctx.author, name)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def removerole(self, ctx: Context, name: str, *, identifier: str) -> None:
        """
        *removerole <role> <identifier>

        A command that removes a role from a member by name, nickname or ID.
        """

        member = await member_get(ctx, identifier)

        if member is None:
            return

        role = discord.utils.get(ctx.guild.roles, name=name)

        if role is None:
            message = f'Role "{name}" not found.'
            await ctx.send(message)

            return

        try:
            await member.remove_roles(role)
        except discord.HTTPException:
            message = f'The {role} role could not be removed from {member}.'
            await ctx.send(message)
        else:
            message = '%s removed the role %s from %s.'
            log.info(message, ctx.author, role, member)

    @commands.hybrid_command(description='Display an overview of a role.')
    @app_commands.describe(identifier='The role by name or ID.')
    @app_commands.autocomplete(identifier=role_autocomplete)
    async def role(self, ctx: Context, *, identifier: str) -> None:
        """
        *role <identifier>

        A command that displays an overview of a role.
        """

        await ctx.typing()

        try:
            role_identifier = await self.roles.identifier_resolve(identifier)
        except DiscordRoleError:
            message = 'No role found.'
            await ctx.send(message)

            return

        role = await self.roles.record_get(role_identifier)

        if role is None:
            message = 'No role found.'
            await ctx.send(message)

            return

        view = RoleCard(role, self.viking.colour)
        await ctx.send(view=view)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def rolepanel(self, ctx: Context) -> None:
        """
        *rolepanel

        A command that posts a self-service role panel. Select the roles
        to include and members can toggle them with a button that survives
        a restart.
        """

        view = RolePanelBuilderView(ctx.author.id)

        content = 'Select the roles to include in the panel:'
        message = await ctx.send(content, view=view)
        view.message = message


async def setup(viking: Viking) -> None:
    viking.add_dynamic_items(RoleToggleButton)

    roles = Roles(viking)
    await viking.add_cog(roles)
