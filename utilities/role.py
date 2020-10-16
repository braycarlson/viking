from database.model import database, GuildRoles


class RoleError(Exception):
    """
    A RoleError is raised when a role is not found in the database
    from user input. This can include by an ID or name.
    """

    pass


class Role:
    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.colour = data.get('colour')
        self.hoist = data.get('hoist')
        self.position = data.get('position')
        self.managed = data.get('managed')
        self.mentionable = data.get('mentionable')
        self.is_default = data.get('is_default')
        self.created_at = data.get('created_at')

    @property
    def created(self):
        return self.created_at.strftime('%B %d, %Y')


async def check_for_role(self, name):
    """
    A function to check for the existence of a role.
    """

    name = name.lower()

    role = (
        await GuildRoles
        .query
        .where(database.func.lower(GuildRoles.name) == name)
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
            await GuildRoles
            .select('id')
            .where(GuildRoles.id == role_id)
            .gino
            .scalar()
        )

        if row is None:
            raise RoleError

        return row


async def get_role_by_name(self, role_name):
    """
    A function to get a role by name from the database.
    """

    row = (
        await GuildRoles
        .query
        .where(database.func.lower(GuildRoles.name) == role_name)
        .gino
        .scalar()
    )

    if row is None:
        raise RoleError

    return row
