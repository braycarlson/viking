from dataclasses import dataclass


@dataclass
class DiscordMemberError(Exception):
    """
    A MemberError is raised when a member is not found in the database
    from user input. This can include by an ID, account name, nickname
    or discriminator.
    """

    pass


@dataclass
class DiscordMember:
    def __init__(self, data):
        self.id = data.get('discord_id')
        self.name = data.get('name')
        self.discriminator = data.get('discriminator')
        self.display_name = data.get('display_name')
        self.nickname = data.get('nickname')
        self.role_id = data.get('role_id')
        self.bot = data.get('bot')
        self.previous_name = data.get('previous_name')
        self.previous_discriminator = data.get('previous_discriminator')
        self.previous_nickname = data.get('previous_nickname')
        self.created_at = data.get('created_at')
        self.joined_at = data.get('joined_at')
        self.updated_at = data.get('updated_at')
        self.removed_at = data.get('removed_at')
        self.banned_at = data.get('banned_at')

    @property
    def created(self):
        return self.created_at.strftime('%B %d, %Y')

    @property
    def joined(self):
        return self.joined_at.strftime('%B %d, %Y')

    @property
    def updated(self):
        return self.updated_at.strftime('%B %d, %Y')

    @property
    def removed(self):
        return self.removed_at.strftime('%B %d, %Y')

    @property
    def banned(self):
        return self.banned_at.strftime('%B %d, %Y')
