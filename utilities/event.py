import discord

from datetime import datetime
from utilities.member import DiscordMember


class MemberEvent:
    def __init__(self, viking):
        self.viking = viking

    # Member Checks

    async def is_member_banned(self, member):
        condition = (
            (self.viking.guild.member.discord_id == member) &
            (self.viking.guild.member.banned_at.is_(None))
        )

        return (
            await self.viking.guild.member
            .query
            .where(condition)
            .gino
            .first()
        )

    async def is_member_removed(self, member):
        condition = (
            (self.viking.guild.member.discord_id == member) &
            (self.viking.guild.member.removed_at.is_(None))
        )

        return (
            await self.viking.guild.member
            .query
            .where(condition)
            .gino
            .first()
        )

    # Member Events

    async def member_create(self, member):
        await self.viking.guild.member.create(
            discord_id=member.id,
            name=member.name,
            discriminator=member.discriminator,
            display_name=member.display_name,
            nickname=member.nick,
            role_id=None,
            bot=member.bot,
            created_at=member.created_at,
            joined_at=member.joined_at
        )

    async def member_ban(self, member):
        banned_at = datetime.now()

        (
            await self.viking.guild.member
            .update
            .values(banned_at=banned_at)
            .where(self.viking.guild.member.discord_id == member)
            .gino
            .status()
        )

    async def member_unban(self, member):
        banned_at = None

        (
            await self.viking.guild.member
            .update
            .values(banned_at=banned_at)
            .where(self.viking.guild.member.discord_id == member)
            .gino
            .status()
        )

    async def member_remove(self, member):
        removed_at = datetime.now()

        (
            await self.viking.guild.member
            .update
            .values(removed_at=removed_at)
            .where(self.viking.guild.member.discord_id == member)
            .gino
            .status()
        )

    async def member_restore(self, member):
        removed_at = None

        (
            await self.viking.guild.member
            .update
            .values(removed_at=removed_at)
            .where(self.viking.guild.member.discord_id == member)
            .gino
            .status()
        )


    # Member Attributes

    # The 'update' functions will be called when a member updates their
    # name, discriminator or nickname for the first time in the server.
    # This will just update their attributes.

    async def name_update(self, before, after):
        now = datetime.now()

        (
            await self.viking.guild.member
            .update
            .values(
                name=after.name,
                display_name=after.display_name,
                updated_at=now
            )
            .where(self.viking.guild.member.discord_id == after.id)
            .gino
            .status()
        )

    async def discriminator_update(self, before, after):
        now = datetime.now()

        (
            await self.viking.guild.member
            .update
            .values(
                discriminator=after.discriminator,
                updated_at=now
            )
            .where(self.viking.guild.member.discord_id == after.id)
            .gino
            .status()
        )

    async def nickname_update(self, before, after):
        now = datetime.now()

        (
            await self.viking.guild.member
            .update
            .values(
                nickname=after.nick,
                display_name=after.display_name,
                updated_at=now
            )
            .where(self.viking.guild.member.discord_id == after.id)
            .gino
            .status()
        )

    async def member_role_update(self, before, after):
        updated_at = datetime.now()

        (
            await self.viking.guild.member
            .update
            .values(
                role_id=after.top_role.id,
                updated_at=updated_at
            )
            .where(self.viking.guild.member.discord_id == after.id)
            .gino
            .status()
        )

    # The 'append' functions will be called when a member updates their
    # name, discriminator or nickname more than once in the server. This
    # will store their old attributes in an array.

    async def name_append(self, before, after):
        now = datetime.now()

        (
            await self.viking.guild.member
            .update
            .values(
                name=after.name,
                previous_name=self.viking.guild.engine.func.array_prepend(
                    before.name,
                    self.viking.guild.member.previous_name
                ),
                display_name=after.display_name,
                updated_at=now
            )
            .where(self.viking.guild.member.discord_id == after.id)
            .gino
            .status()
        )

    async def discriminator_append(self, before, after):
        now = datetime.now()

        (
            await self.viking.guild.member
            .update
            .values(
                discriminator=after.discriminator,
                previous_discriminator=self.viking.guild.engine.func.array_prepend(
                    before.discriminator,
                    self.viking.guild.member.previous_discriminator
                ),
                updated_at=now
            )
            .where(self.viking.guild.member.discord_id == after.id)
            .gino
            .status()
        )

    async def nickname_append(self, before, after):
        now = datetime.now()

        (
            await self.viking.guild.member
            .update
            .values(
                nickname=after.nick,
                previous_nickname=self.viking.guild.engine.func.array_prepend(
                    before.nick,
                    self.viking.guild.member.previous_nickname
                ),
                display_name=after.display_name,
                updated_at=now
            )
            .where(self.viking.guild.member.discord_id == after.id)
            .gino
            .status()
        )

    # These functions will handle the case where a member is kicked
    # from the server, and updates their information while they're
    # kicked. If the member rejoins the server, their database record
    # will be updated and/or appended to.

    async def get_old_record(self, member):
        row = (
            await self.viking.guild.member.select(
                'name',
                'discriminator',
                'nickname',
                'removed_at',
                'banned_at'
            )
            .where(self.viking.guild.member.discord_id == member)
            .gino
            .first()
        )

        return dict(row)

    async def old_name_update(self, member, name):
        if name != member.name:
            (
                await self.viking.guild.member
                .update
                .values(
                    previous_name=self.viking.guild.engine.func.array_prepend(
                        name,
                        self.viking.guild.member.previous_name
                    ),
                )
                .where(self.viking.guild.member.discord_id == member.id)
                .gino
                .status()
            )

    async def old_discriminator_update(self, member, discriminator):
        if discriminator != member.discriminator:
            (
                await self.viking.guild.member
                .update
                .values(
                    previous_discriminator=self.viking.guild.engine.func.array_prepend(
                        discriminator,
                        self.viking.guild.member.previous_discriminator
                    ),
                ).where(self.viking.guild.member.discord_id == member.id)
                .gino
                .status()
            )

    async def old_nickname_update(self, member, nickname):
        if nickname != member.nick:
            (
                await self.viking.guild.member
                .update
                .values(
                    previous_nickname=self.viking.guild.engine.func.array_prepend(
                        nickname,
                        self.viking.guild.member.previous_nickname
                    ),
                )
                .where(self.viking.guild.member.discord_id == member.id)
                .gino
                .status()
            )

    async def member_update(self, member):
        joined_at, updated_at = datetime.now(), datetime.now()
        row = await self.get_old_record(member.id)
        old = DiscordMember(row)

        await self.old_name_update(member, old.name)
        await self.old_discriminator_update(member, old.discriminator)
        await self.old_nickname_update(member, old.nickname)

        (
            await self.viking.guild.member
            .update
            .values(
                name=member.name,
                discriminator=member.discriminator,
                display_name=member.display_name,
                nickname=member.nick,
                role_id=None,
                joined_at=joined_at,
                updated_at=updated_at,
                removed_at=old.removed_at,
                banned_at=old.banned_at
            )
            .where(self.viking.guild.member.discord_id == member.id)
            .gino
            .status()
        )


class RoleEvent:
    def __init__(self, viking):
        self.viking = viking

    async def role_create(self, role):
        await self.viking.guild.role.create(
            id=role.id,
            name=role.name,
            colour=str(role.colour),
            hoist=role.hoist,
            position=role.position,
            managed=role.managed,
            mentionable=role.mentionable,
            is_default=role.is_default(),
            created_at=role.created_at
        )

    async def role_add(self):
        rows = (
            await self.viking.guild.member
            .select('discord_id')
            .where(self.viking.guild.member.role_id == 186994904365400064)
            .gino
            .all()
        )

        for guild in self.viking.guilds:
            role = discord.utils.get(guild.roles, id=self.viking.normal)

        for row in rows:
            row = dict(row)
            discord_id = row.get('discord_id')
            member = guild.get_member(discord_id)
            await member.add_roles(role)

    async def role_update(self, role):
        (
            await self.viking.guild.role
            .update
            .values(
                id=role.id,
                name=role.name,
                colour=str(role.colour),
                hoist=role.hoist,
                position=role.position,
                managed=role.managed,
                mentionable=role.mentionable,
                is_default=role.is_default(),
                created_at=role.created_at
            )
            .where(self.viking.guild.role.id == role.id)
            .gino
            .status()
        )

    async def role_delete(self, role_id):
        (
            await self.viking.guild.role
            .delete
            .where(self.viking.guild.role.id == role_id)
            .gino
            .status()
        )

    async def role_replace(self, after):
        updated_at = datetime.now()

        for guild in self.viking.guilds:
            for member in guild.members:
                row = (
                    await self.viking.guild.member
                    .select('role_id')
                    .where(self.viking.guild.member.discord_id == member.id)
                    .gino
                    .scalar()
                )

                if row != member.top_role.id:
                    (
                        await self.viking.guild.member
                        .update
                        .values(
                            role_id=after.id,
                            updated_at=updated_at
                        )
                        .where(self.viking.guild.member.discord_id == member.id)
                        .gino
                        .status()
                    )
