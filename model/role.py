from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DiscordRoleError(Exception):
    """
    A RoleError is raised when a role is not found in the database
    from user input. This can include by an ID or name.
    """


@dataclass
class DiscordRole:
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
    def created(self) -> str:
        return self.created_at.strftime('%B %d, %Y')
