from __future__ import annotations

from database.base import Member, Role, Sound
from database.engine import nac, nd


class Member(Member, nac.Model):
    __tablename__ = 'member'

    _fk_role_id = nac.ForeignKeyConstraint(['role_id'], ['role.id'])
    _idx_member_name = nac.Index('index_member_name', nac.func.lower('name'))
    _idx_member_nickname = nac.Index('index_member_nickname', nac.func.lower('nickname'))


class Role(Role, nac.Model):
    __tablename__ = 'role'

    _idx_role_id = nac.Index('index_role_id', 'id', unique=True)
    _idx_role_name = nac.Index('index_role_name', nac.func.lower('name'))


class Sound(Sound, nac.Model):
    __tablename__ = 'sound'

    _fk_discord_id = nac.ForeignKeyConstraint(['created_by'], ['member.discord_id'])
    _idx_name = nac.Index('index_name', nac.func.lower('name'))


nd.engine = nac
nd.member = Member
nd.role = Role
nd.sound = Sound
