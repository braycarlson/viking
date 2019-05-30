import discord
import logging
from discord.ext import commands
from utilities.event import RoleEvent
from utilities.member import MemberError, get_member_by_id
from utilities.role import Role, RoleError, get_role_by_id, check_for_role

log = logging.getLogger(__name__)


class Roles(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.event = RoleEvent(self.viking)

    # Event Listeners

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        """
        An event that is called when a role is created.
        """

        await self.event.role_create(role)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """
        An event that is called when a role is deleted.
        """

        await self.event.role_add()
        await self.event.role_delete(role.id)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        """
        An event that is called when a role is updated.
        """

        await self.event.role_update(after)

        # If the role hierarchy is rearranged, assign the role with the
        # higher position as the top role in the database.

        if before.position < after.position:
            await self.event.role_replace(after)

    # Commands

    @commands.command(hidden=True)
    @commands.has_any_role('Administrator')
    async def addrole(self, ctx, name: str, *, identifier: str):
        """
        *addrole <role> <identifier>

        A command that adds a role to a member by name, nickname or ID.
        """

        try:
            member_id = await get_member_by_id(self, ctx, identifier)
        except MemberError:
            await ctx.send('No member found.')
        except TimeoutError:
            await ctx.send('You have run out of time. Please try again.')
        else:
            member = ctx.guild.get_member(member_id)
            role = discord.utils.get(ctx.guild.roles, name=name)

            try:
                await member.add_roles(role)
            except discord.HTTPException:
                await ctx.send(f"{member} could not be assigned the {role} role.")
            else:
                log.info(f"{ctx.author} assigned the role {role} to {member}.")

    @commands.command(hidden=True)
    @commands.has_any_role('Administrator')
    async def createrole(self, ctx, *, name: str):
        """
        *createrole <name>

        A command that creates a role with no permissions.
        """

        check = await check_for_role(self, name)

        if check is False:
            try:
                permissions = discord.Permissions.none()
                await ctx.guild.create_role(name=name, permissions=permissions)
            except discord.HTTPException:
                await ctx.send(f"{name} could not be created.")
            else:
                log.info(f"{ctx.author} created the role {name}.")
        else:
            await ctx.send(f"Please use another name.")

    @commands.command(hidden=True)
    @commands.has_any_role('Administrator')
    async def deleterole(self, ctx, *, name: str):
        """
        *deleterole <name>

        A command that deletes a role.
        """

        check = await check_for_role(self, name)

        if check is True:
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
    @commands.has_any_role('Administrator')
    async def removerole(self, ctx, name: str, *, identifier: str):
        """
        *removerole <role> <identifier>

        A command that removes a role from a member by name, nickname or ID.
        """

        try:
            member_id = await get_member_by_id(self, ctx, identifier)
        except MemberError:
            await ctx.send('No member found.')
        except TimeoutError:
            await ctx.send('You have run out of time. Please try again.')
        else:
            member = ctx.guild.get_member(member_id)
            role = discord.utils.get(ctx.guild.roles, name=name)

            try:
                await member.remove_roles(role)
            except discord.HTTPException:
                await ctx.send(f"The {role} role could not be removed from {member}.")
            else:
                log.info(f"{ctx.author} removed the role {role} from {member}.")

    @commands.command()
    async def role(self, ctx, *, identifier: str):
        """
        *role <identifier>

        A command that displays an overview of a role.
        """

        try:
            role_id = await get_role_by_id(self, identifier)
        except RoleError:
            await ctx.send('No role found.')
        else:
            embed = discord.Embed(color=self.viking.color)

            async with self.viking.postgresql.acquire() as connection:
                query = """
                        SELECT *
                        FROM roles
                        WHERE id = $1
                        """

                rows = await connection.fetch(query, role_id)

                for row in rows:
                    role = Role(row)

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


def setup(viking):
    viking.add_cog(Roles(viking))
