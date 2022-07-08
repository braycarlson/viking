import discord
import logging

from database.viking import Role
from discord.ext import commands
from model.role import DiscordRole, DiscordRoleError
from utilities.event import RoleEvent
from utilities.member import MemberInterface
from utilities.role import (
    check_for_role,
    get_role_by_id
)


log = logging.getLogger(__name__)


class Roles(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.event = RoleEvent(self.viking)

    # Event Listeners

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """
        An event that is called when a role is created.
        """

        await self.viking.update(role.guild.id)
        await self.event.role_create(role)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """
        An event that is called when a role is deleted.
        """

        await self.viking.update(role.guild.id)
        await self.event.role_add()
        await self.event.role_delete(role.id)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """
        An event that is called when a role is updated.
        """

        await self.viking.update(before.guild.id)
        await self.event.role_update(after)

        # If the role hierarchy is changed, assign the role with the
        # higher position as the top role in the database.

        if before < after:
            await self.event.role_replace(after)

    # Commands

    @commands.command(hidden=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, name, *, identifier):
        """
        *addrole <role> <identifier>

        A command that adds a role to a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = ctx.guild.get_member(discord_id)
        role = discord.utils.get(ctx.guild.roles, name=name)

        try:
            await member.add_roles(role)
        except discord.HTTPException:
            await ctx.send(f"{member} could not be assigned the {role} role.")
        else:
            log.info(f"{ctx.author} assigned the role {role} to {member}.")

    @commands.command(hidden=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    async def createrole(self, ctx, *, name):
        """
        *createrole <name>

        A command that creates a role with no permissions.
        """

        check = await check_for_role(self, name)

        if check is None:
            try:
                permissions = discord.Permissions.none()
                await ctx.guild.create_role(name=name, permissions=permissions)
            except discord.HTTPException:
                await ctx.send(f"{name} could not be created.")
            else:
                log.info(f"{ctx.author} created the role {name}.")
        else:
            await ctx.send('A role with that name already exists.')

    @commands.command(hidden=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    async def deleterole(self, ctx, *, name):
        """
        *deleterole <name>

        A command that deletes a role.
        """

        check = await check_for_role(self, name)

        if check is not None:
            for guild in self.viking.guilds:
                role = discord.utils.get(guild.roles, name=name)

            try:
                await role.delete()
            except discord.HTTPException:
                return await ctx.send(f"{name} could not be deleted.")
            else:
                log.info(f"{ctx.author} deleted the role {name}.")
        else:
            await ctx.send('No role found.')

    @commands.command(hidden=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, name, *, identifier):
        """
        *removerole <role> <identifier>

        A command that removes a role from a member by name, nickname or ID.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return

        member = ctx.guild.get_member(discord_id)
        role = discord.utils.get(ctx.guild.roles, name=name)

        try:
            await member.remove_roles(role)
        except discord.HTTPException:
            await ctx.send(f"The {role} role could not be removed from {member}.")
        else:
            log.info(f"{ctx.author} removed the role {role} from {member}.")

    @commands.command()
    async def role(self, ctx, *, identifier):
        """
        *role <identifier>

        A command that displays an overview of a role.
        """

        try:
            role_id = await get_role_by_id(self, identifier)
        except DiscordRoleError:
            await ctx.send('No role found.')
        else:
            embed = discord.Embed(color=self.viking.color)

            row = dict(
                await Role
                .query.execution_options(return_model=False)
                .where(Role.id == role_id)
                .gino.first()
            )

            role = DiscordRole(row)

            embed.add_field(
                inline=False,
                name='Role ID',
                value=role.id
            )
            embed.add_field(
                inline=False,
                name='Name',
                value=role.name
            )
            embed.add_field(
                inline=False,
                name='Colour',
                value=role.colour
            )
            embed.add_field(
                inline=False,
                name='Hoist',
                value=role.hoist
            )
            embed.add_field(
                inline=False,
                name='Position',
                value=role.position
            )
            embed.add_field(
                inline=False,
                name='Mentionable',
                value=role.mentionable
            )
            embed.add_field(
                inline=False,
                name='Created At',
                value=role.created
            )

            await ctx.send(embed=embed)


async def setup(viking):
    roles = Roles(viking)
    await viking.add_cog(roles)
