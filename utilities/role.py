from model.role import DiscordRoleError
from sqlalchemy import func


async def check_for_role(self, name):
    """
    A function to check for the existence of a role.
    """

    name = name.lower()

    role = (
        await self.viking.guild.role
        .query
        .where(func.lower(self.viking.guild.role.name) == name)
        .gino
        .scalar()
    )

    return role


async def get_role_by_id(self, identifier):
    """
    A function to get a role by ID from the database.
    """

    try:
        role_id = int(identifier)
    except ValueError:
        role = identifier.lower()
        return await get_role_by_name(self, role)
    else:
        row = (
            await self.viking.guild.role
            .select('id')
            .where(self.viking.guild.role.id == role_id)
            .gino
            .scalar()
        )

        if row is None:
            raise DiscordRoleError

        return row


async def get_role_by_name(self, role_name):
    """
    A function to get a role by name from the database.
    """

    row = (
        await self.viking.guild.role
        .query
        .where(func.lower(self.viking.guild.role.name) == role_name)
        .gino
        .scalar()
    )

    if row is None:
        raise DiscordRoleError

    return row
