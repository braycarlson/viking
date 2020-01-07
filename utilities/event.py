import discord
from database.model import (
    database,
    ActiveMembers,
    BannedMembers,
    GuildRoles,
    RemovedMembers
)
from datetime import datetime
from utilities.member import Member


class MemberEvent:
    def __init__(self, viking):
        self.viking = viking

    # Member Checks

    async def is_member_banned(self, member: int):
        return await BannedMembers.query.where(
            BannedMembers.discord_id == member
        ).gino.first()

    async def is_member_removed(self, member: int):
        return await RemovedMembers.query.where(
            RemovedMembers.discord_id == member
        ).gino.first()

    # Member Events

    async def member_create(self, member: discord.Member):

        await ActiveMembers.create(
            discord_id=member.id,
            name=member.name,
            discriminator=member.discriminator,
            display_name=member.display_name,
            nickname=member.nick,
            role_id=self.viking.normal,
            bot=member.bot,
            created_at=member.created_at,
            joined_at=member.joined_at
        )

    async def member_ban(self, member: int):
        now = datetime.now()

        await BannedMembers.insert().from_select(
            BannedMembers.__table__.columns.keys(),
            database.select('*').where(ActiveMembers.discord_id == member)
        ).gino.status()

        await BannedMembers.update.values(
            deleted_at=now
        ).where(BannedMembers.discord_id == member).gino.status()

    async def member_unban(self, member: int):
        now = datetime.now()

        await RemovedMembers.insert().from_select(
            RemovedMembers.__table__.columns.keys(),
            database.select('*').where(BannedMembers.discord_id == member)
        ).gino.status()

        await RemovedMembers.update.values(
            removed_at=now
        ).where(RemovedMembers.discord_id == member).gino.status()

    async def member_remove(self, member: int):
        now = datetime.now()

        await RemovedMembers.insert().from_select(
            RemovedMembers.__table__.columns.keys(),
            database.select('*').where(ActiveMembers.discord_id == member)
        ).gino.status()

        await RemovedMembers.update.values(
            removed_at=now
        ).where(RemovedMembers.discord_id == member).gino.status()

    async def member_restore(self, member: int):
        await ActiveMembers.insert().from_select(
            ActiveMembers.__table__.columns.keys(),
            database.select('*').where(RemovedMembers.discord_id == member)
        ).gino.status()

    async def member_delete(self, member: int, table='members'):
        if table == 'members':
            await ActiveMembers.delete.where(
                ActiveMembers.discord_id == member
            ).gino.status()

        if table == 'banned_members':
            await BannedMembers.delete.where(
                BannedMembers.discord_id == member
            ).gino.status()

        if table == 'removed_members':
            await RemovedMembers.delete.where(
                RemovedMembers.discord_id == member
            ).gino.status()

    # Member Attributes

    # The 'update' functions will be called when a member updates their
    # name, discriminator or nickname for the first time in the server.
    # This will just update their attributes.

    async def name_update(self, before: discord.User, after: discord.User):
        now = datetime.now()

        await ActiveMembers.update.values(
            name=after.name,
            display_name=after.display_name,
            updated_at=now
        ).where(ActiveMembers.discord_id == after.id).gino.status()

    async def discriminator_update(self, before: discord.User, after: discord.User):
        now = datetime.now()

        await ActiveMembers.update.values(
            discriminator=after.discriminator,
            updated_at=now
        ).where(ActiveMembers.discord_id == after.id).gino.status()

    async def nickname_update(self, before: discord.Member, after: discord.Member):
        now = datetime.now()

        await ActiveMembers.update.values(
            nickname=after.nick,
            display_name=after.display_name,
            updated_at=now
        ).where(ActiveMembers.discord_id == after.id).gino.status()

    async def member_role_update(self, before: discord.Member, after: discord.Member):
        now = datetime.now()

        await ActiveMembers.update.values(
            role_id=after.top_role.id,
            updated_at=now
        ).where(ActiveMembers.discord_id == after.id).gino.status()

    # The 'append' functions will be called when a member updates their
    # name, discriminator or nickname more than once in the server. This
    # will store their old attributes in an array.

    async def name_append(self, before: discord.User, after: discord.User):
        now = datetime.now()

        await ActiveMembers.update.values(
            name=after.name,
            previous_name=database.func.array_prepend(before.name, ActiveMembers.previous_name),
            display_name=after.display_name,
            updated_at=now
        ).where(ActiveMembers.discord_id == after.id).gino.status()

    async def discriminator_append(self, before: discord.User, after: discord.User):
        now = datetime.now()

        await ActiveMembers.update.values(
            discriminator=after.discriminator,
            previous_discriminator=database.func.array_prepend(before.discriminator, ActiveMembers.previous_discriminator),
            updated_at=now
        ).where(ActiveMembers.discord_id == after.id).gino.status()

    async def nickname_append(self, before: discord.Member, after: discord.Member):
        now = datetime.now()

        await ActiveMembers.update.values(
            nickname=after.nick,
            previous_nickname=database.func.array_prepend(before.nick, ActiveMembers.previous_nickname),
            display_name=after.display_name,
            updated_at=now
        ).where(ActiveMembers.discord_id == after.id).gino.status()

    # These functions will handle the case where a member is kicked
    # from the server, and updates their information while they're
    # kicked. If the member rejoins the server, their database record
    # will be updated and/or appended to.

    async def get_old_record(self, member: int):
        row = await ActiveMembers.select(
            'name',
            'discriminator',
            'nickname',
            'removed_at',
            'deleted_at'
        ).where(ActiveMembers.discord_id == member).gino.first()

        return dict(row)

    async def old_name_update(self, member: discord.Member, name: str):
        if name != member.name:
            await ActiveMembers.update.values(
                previous_name=database.func.array_prepend(name, ActiveMembers.previous_name),
            ).where(ActiveMembers.discord_id == member.id).gino.status()

    async def old_discriminator_update(self, member: discord.Member, discriminator: str):
        if discriminator != member.discriminator:
            await ActiveMembers.update.values(
                previous_discriminator=database.func.array_prepend(discriminator, ActiveMembers.previous_discriminator),
            ).where(ActiveMembers.discord_id == member.id).gino.status()

    async def old_nickname_update(self, member: discord.Member, nickname: str):
        if nickname != member.nick:
            await ActiveMembers.update.values(
                previous_nickname=database.func.array_prepend(nickname, ActiveMembers.previous_nickname),
            ).where(ActiveMembers.discord_id == member.id).gino.status()

    async def member_update(self, member: discord.Member):
        now = datetime.now()
        row = await self.get_old_record(member.id)
        old = Member(row)

        await self.old_name_update(member, old.name)
        await self.old_discriminator_update(member, old.discriminator)
        await self.old_nickname_update(member, old.nickname)

        await ActiveMembers.update.values(
            name=member.name,
            discriminator=member.discriminator,
            display_name=member.display_name,
            nickname=member.nick,
            role_id=self.viking.normal,
            joined_at=now,
            updated_at=now,
            removed_at=old.removed_at,
            deleted_at=old.deleted_at
        ).where(ActiveMembers.discord_id == member.id).gino.status()


class RoleEvent:
    def __init__(self, viking):
        self.viking = viking

    async def role_create(self, role: discord.Role):
        await GuildRoles.create(
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
        rows = await ActiveMembers.select(
            'discord_id'
        ).where(ActiveMembers.role_id == 186994904365400064).gino.all()

        for guild in self.viking.guilds:
            role = discord.utils.get(guild.roles, id=self.viking.normal)

        for row in rows:
            row = dict(row)
            discord_id = row.get('discord_id')
            member = guild.get_member(discord_id)
            await member.add_roles(role)

    async def role_update(self, role: discord.Role):
        await GuildRoles.update.values(
            id=role.id,
            name=role.name,
            colour=str(role.colour),
            hoist=role.hoist,
            position=role.position,
            managed=role.managed,
            mentionable=role.mentionable,
            is_default=role.is_default(),
            created_at=role.created_at
        ).where(GuildRoles.id == role.id).gino.status()

    async def role_delete(self, role_id: int):
        await GuildRoles.delete.where(
            GuildRoles.id == role_id
        ).gino.status()

    async def role_replace(self, after: discord.Role):
        now = datetime.now()

        for guild in self.viking.guilds:
            for member in guild.members:
                row = await ActiveMembers.select('role_id').where(
                    ActiveMembers.discord_id == member.id
                ).gino.scalar()

                if row != member.top_role.id:
                    await ActiveMembers.update.values(
                        role_id=after.id,
                        updated_at=now
                    ).where(ActiveMembers.discord_id == member.id).gino.status()
