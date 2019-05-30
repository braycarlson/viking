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


async def check_for_role(self, name: str):
    """
    A function to check for the existence of a role.
    """

    name = name.lower()

    async with self.viking.postgresql.acquire() as connection:
        query = """
                SELECT
                EXISTS(
                    SELECT id
                    FROM roles
                    WHERE lower(name) = $1
                )
                """

        return await connection.fetchval(query, name)


async def get_role_by_id(self, identifier: str):
    """
    A function to get a role by ID from the database.
    """

    try:
        role_id = int(identifier)
    except ValueError:
        role = identifier.lower()
        return await get_role_by_name(self, role)
    else:
        async with self.viking.postgresql.acquire() as connection:
            query = f"""
                    SELECT id
                    FROM roles
                    WHERE id = $1
                    """

            row = await connection.fetchval(query, role_id)

            if row is None:
                raise RoleError

            return row


async def get_role_by_name(self, role_name: str):
    """
    A function to get a role by name from the database.
    """

    async with self.viking.postgresql.acquire() as connection:
        query = f"""
                SELECT id
                FROM roles
                WHERE lower(name) = $1
                """

        rows = await connection.fetch(query, role_name)

        if len(rows) == 0:
            raise RoleError

        if len(rows) == 1:
            return await connection.fetchval(query, role_name)
