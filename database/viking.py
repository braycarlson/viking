from database.base import Member, Role, Sound
from database.engine import vd, viking


class Member(Member, viking.Model):
    __tablename__ = 'member'

    _fk_role_id = viking.ForeignKeyConstraint(['role_id'], ['role.id'])
    _idx_member_name = viking.Index('index_member_name', viking.func.lower('name'))
    _idx_member_nickname = viking.Index('index_member_nickname', viking.func.lower('nickname'))


class Role(Role, viking.Model):
    __tablename__ = 'role'

    _idx_role_id = viking.Index('index_role_id', 'id', unique=True)
    _idx_role_name = viking.Index('index_role_name', viking.func.lower('name'))


class Sound(Sound, viking.Model):
    __tablename__ = 'sound'

    _fk_discord_id = viking.ForeignKeyConstraint(['created_by'], ['member.discord_id'])
    _idx_name = viking.Index('index_name', viking.func.lower('name'))


vd.engine = viking
vd.member = Member
vd.role = Role
vd.sound = Sound
