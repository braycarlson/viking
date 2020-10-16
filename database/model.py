from gino import Gino


database = Gino()


class MemberSounds(database.Model):
    __tablename__ = 'member_sounds'

    id = database.Column(database.BigInteger(), primary_key=True)
    name = database.Column(database.TEXT(), nullable=False)
    created_by = database.Column(database.BigInteger(), nullable=False)
    created_at = database.Column(database.DateTime(), nullable=True)
    updated_at = database.Column(database.DateTime(), nullable=True)

    _fk_discord_id = database.ForeignKeyConstraint(["created_by"], ["active_members.discord_id"])
    _idx_name = database.Index('index_name', database.func.lower('name'))


class GuildRoles(database.Model):
    __tablename__ = 'guild_roles'

    id = database.Column(database.BigInteger(), primary_key=True)
    name = database.Column(database.TEXT(), nullable=False)
    colour = database.Column(database.VARCHAR(255), nullable=False)
    hoist = database.Column(database.Boolean(), nullable=False)
    position = database.Column(database.SmallInteger(), primary_key=True)
    managed = database.Column(database.Boolean(), nullable=False)
    mentionable = database.Column(database.Boolean(), nullable=False)
    is_default = database.Column(database.Boolean(), nullable=False)
    created_at = database.Column(database.DateTime(), nullable=True)

    _idx_role_id = database.Index('index_role_id', 'id', unique=True)
    _idx_role_name = database.Index('index_role_name', database.func.lower('name'))


class ActiveMembers(database.Model):
    __tablename__ = 'active_members'

    discord_id = database.Column(database.BigInteger(), primary_key=True)
    name = database.Column(database.TEXT(), nullable=False)
    discriminator = database.Column(database.VARCHAR(255), nullable=False)
    display_name = database.Column(database.TEXT(), nullable=False)
    nickname = database.Column(database.TEXT(), nullable=True)
    role_id = database.Column(database.BigInteger(), nullable=False)
    bot = database.Column(database.Boolean(), nullable=False)
    previous_name = database.Column(database.ARRAY(database.TEXT()), nullable=True)
    previous_discriminator = database.Column(database.ARRAY(database.VARCHAR(255)), nullable=True)
    previous_nickname = database.Column(database.ARRAY(database.TEXT()), nullable=True)
    created_at = database.Column(database.DateTime(), nullable=True)
    joined_at = database.Column(database.DateTime(), nullable=True)
    updated_at = database.Column(database.DateTime(), nullable=True)
    removed_at = database.Column(database.DateTime(), nullable=True)
    deleted_at = database.Column(database.DateTime(), nullable=True)

    _fk_role_id = database.ForeignKeyConstraint(["role_id"], ["guild_roles.id"])
    _idx_member_name = database.Index('index_member_name', database.func.lower('name'))
    _idx_member_nickname = database.Index('index_member_nickname', database.func.lower('nickname'))


class RemovedMembers(database.Model):
    __tablename__ = 'removed_members'

    discord_id = database.Column(database.BigInteger(), primary_key=True)
    name = database.Column(database.TEXT(), nullable=False)
    discriminator = database.Column(database.VARCHAR(255), nullable=False)
    display_name = database.Column(database.TEXT(), nullable=False)
    nickname = database.Column(database.TEXT(), nullable=True)
    role_id = database.Column(database.BigInteger(), nullable=False)
    bot = database.Column(database.Boolean(), nullable=False)
    previous_name = database.Column(database.ARRAY(database.TEXT()), nullable=True)
    previous_discriminator = database.Column(database.ARRAY(database.VARCHAR(255)), nullable=True)
    previous_nickname = database.Column(database.ARRAY(database.TEXT()), nullable=True)
    created_at = database.Column(database.DateTime(), nullable=True)
    joined_at = database.Column(database.DateTime(), nullable=True)
    updated_at = database.Column(database.DateTime(), nullable=True)
    removed_at = database.Column(database.DateTime(), nullable=True)
    deleted_at = database.Column(database.DateTime(), nullable=True)

    _fk_role_id = database.ForeignKeyConstraint(["role_id"], ["guild_roles.id"])
    _idx_removed_member_name = database.Index('index_removed_member_name', database.func.lower('name'))
    _idx_removed_member_nickname = database.Index('index_removed_member_nickname', database.func.lower('nickname'))


class BannedMembers(database.Model):
    __tablename__ = 'banned_members'

    discord_id = database.Column(database.BigInteger(), primary_key=True)
    name = database.Column(database.TEXT(), nullable=False)
    discriminator = database.Column(database.VARCHAR(255), nullable=False)
    display_name = database.Column(database.TEXT(), nullable=False)
    nickname = database.Column(database.TEXT(), nullable=True)
    role_id = database.Column(database.BigInteger(), nullable=False)
    bot = database.Column(database.Boolean(), nullable=False)
    previous_name = database.Column(database.ARRAY(database.TEXT()), nullable=True)
    previous_discriminator = database.Column(database.ARRAY(database.VARCHAR(255)), nullable=True)
    previous_nickname = database.Column(database.ARRAY(database.TEXT()), nullable=True)
    created_at = database.Column(database.DateTime(), nullable=True)
    joined_at = database.Column(database.DateTime(), nullable=True)
    updated_at = database.Column(database.DateTime(), nullable=True)
    removed_at = database.Column(database.DateTime(), nullable=True)
    deleted_at = database.Column(database.DateTime(), nullable=True)

    _fk_role_id = database.ForeignKeyConstraint(["role_id"], ["guild_roles.id"])
    _idx_banned_member_name = database.Index('index_banned_member_name', database.func.lower('name'))
    _idx_banned_member_nickname = database.Index('index_banned_member_nickname', database.func.lower('nickname'))


class PublicCommands(database.Model):
    __tablename__ = 'public_commands'

    id = database.Column(database.Integer(), primary_key=True)
    name = database.Column(database.TEXT(), nullable=False)
    aliases = database.Column(database.ARRAY(database.TEXT()), nullable=True)

    _idx_public_command_name = database.Index('index_public_command_name', 'name', unique=True)


class HiddenCommands(database.Model):
    __tablename__ = 'hidden_commands'

    id = database.Column(database.Integer(), primary_key=True)
    name = database.Column(database.TEXT(), nullable=False)
    aliases = database.Column(database.ARRAY(database.TEXT()), nullable=True)

    _idx_hidden_command_name = database.Index('index_hidden_command_name', 'name', unique=True)


class NHLTeams(database.Model):
    __tablename__ = 'nhl_teams'

    team_id = database.Column(database.Integer(), primary_key=True)
    name = database.Column(database.TEXT(), nullable=False)
    link = database.Column(database.TEXT(), nullable=False)
    venue_id = database.Column(database.Integer(), nullable=True)
    venue_name = database.Column(database.TEXT(), nullable=False)
    venue_link = database.Column(database.TEXT(), nullable=False)
    venue_city = database.Column(database.TEXT(), nullable=False)
    timezone_id = database.Column(database.TEXT(), nullable=False)
    timezone_offset = database.Column(database.Integer(), nullable=False)
    timezone_tz = database.Column(database.TEXT(), nullable=False)
    abbreviation = database.Column(database.TEXT(), nullable=False)
    team_name = database.Column(database.TEXT(), nullable=False)
    location_name = database.Column(database.TEXT(), nullable=False)
    first_year_of_play = database.Column(database.TEXT(), nullable=False)
    division_id = database.Column(database.Integer(), nullable=False)
    division_name = database.Column(database.TEXT(), nullable=False)
    division_name_short = database.Column(database.TEXT(), nullable=False)
    division_link = database.Column(database.TEXT(), nullable=False)
    division_abbreviation = database.Column(database.TEXT(), nullable=False)
    conference_id = database.Column(database.Integer(), nullable=False)
    conference_name = database.Column(database.TEXT(), nullable=False)
    conference_link = database.Column(database.TEXT(), nullable=False)
    franchise_id = database.Column(database.Integer(), nullable=False)
    franchise_name = database.Column(database.TEXT(), nullable=False)
    franchise_link = database.Column(database.TEXT(), nullable=False)
    short_name = database.Column(database.TEXT(), nullable=False)
    official_website = database.Column(database.TEXT(), nullable=False)
    active = database.Column(database.Boolean(), nullable=False)

    _idx_nhl_team_name = database.Index('index_nhl_team_name', 'name', unique=True)
    _idx_nhl_team_abbreviation = database.Index('index_nhl_team_abbreviation', 'abbreviation', unique=True)


class NHLPlayers(database.Model):
    __tablename__ = 'nhl_players'

    player_id = database.Column(database.BigInteger(), primary_key=True)
    full_name = database.Column(database.TEXT(), nullable=False)
    link = database.Column(database.TEXT(), nullable=False)
    first_name = database.Column(database.TEXT(), nullable=False)
    last_name = database.Column(database.TEXT(), nullable=False)
    number = database.Column(database.TEXT(), nullable=False)
    birthdate = database.Column(database.TEXT(), nullable=False)
    age = database.Column(database.Integer(), nullable=False)
    city = database.Column(database.TEXT(), nullable=False)
    province = database.Column(database.TEXT(), nullable=True)
    country = database.Column(database.TEXT(), nullable=False)
    nationality = database.Column(database.TEXT(), nullable=False)
    height = database.Column(database.TEXT(), nullable=False)
    weight = database.Column(database.Integer(), nullable=False)
    active = database.Column(database.Boolean(), nullable=False)
    alternate_captain = database.Column(database.Boolean(), nullable=False)
    captain = database.Column(database.Boolean(), nullable=False)
    rookie = database.Column(database.Boolean(), nullable=False)
    shooting_hand = database.Column(database.TEXT(), nullable=False)
    team_id = database.Column(database.Integer(), nullable=True)
    team_name = database.Column(database.TEXT(), nullable=True)
    team_link = database.Column(database.TEXT(), nullable=True)
    position_code = database.Column(database.TEXT(), nullable=True)
    position_name = database.Column(database.TEXT(), nullable=True)
    position_type = database.Column(database.TEXT(), nullable=True)
    position_abbreviation = database.Column(database.TEXT(), nullable=True)

    _fk_team_id = database.ForeignKeyConstraint(["team_id"], ["nhl_teams.team_id"])


class LoLChampions(database.Model):
    __tablename__ = 'lol_champions'

    champion_id = database.Column(database.TEXT(), primary_key=True)
    name = database.Column(database.TEXT(), nullable=False)
    title = database.Column(database.TEXT(), nullable=False)
    blurb = database.Column(database.TEXT(), nullable=False)
    attack_information = database.Column(database.Integer(), nullable=False)
    defense_information = database.Column(database.Integer(), nullable=False)
    magic_information = database.Column(database.Integer(), nullable=False)
    difficulty_information = database.Column(database.Integer(), nullable=False)
    full_image = database.Column(database.TEXT(), nullable=False)
    champion_class = database.Column(database.TEXT(), nullable=False)
    resource = database.Column(database.TEXT(), nullable=True)
    health = database.Column(database.Integer(), nullable=False)
    health_per_level = database.Column(database.Integer(), nullable=False)
    mana = database.Column(database.Integer(), nullable=False)
    mana_per_level = database.Column(database.Integer(), nullable=False)
    movement_speed = database.Column(database.Integer(), nullable=False)
    armor = database.Column(database.Integer(), nullable=False)
    armor_per_level = database.Column(database.Integer(), nullable=False)
    spellblock = database.Column(database.Integer(), nullable=False)
    spellblock_per_level = database.Column(database.Integer(), nullable=False)
    attack_range = database.Column(database.Integer(), nullable=False)
    health_regeneration = database.Column(database.Integer(), nullable=False)
    health_regeneration_per_level = database.Column(database.Integer(), nullable=False)
    mana_regeneration = database.Column(database.Integer(), nullable=False)
    mana_regeneration_per_level = database.Column(database.Integer(), nullable=False)
    critical_strike = database.Column(database.Integer(), nullable=False)
    critical_strike_per_level = database.Column(database.Integer(), nullable=False)
    attack_damage = database.Column(database.Integer(), nullable=False)
    attack_damage_per_level = database.Column(database.Integer(), nullable=False)
    attack_speed_per_level = database.Column(database.Integer(), nullable=False)
    attack_speed = database.Column(database.Integer(), nullable=False)


class LoLSpells(database.Model):
    __tablename__ = 'lol_spells'

    spell_id = database.Column(database.TEXT(), nullable=False)
    spell_key = database.Column(database.TEXT(), nullable=False)
    name = database.Column(database.TEXT(), nullable=False)
    description = database.Column(database.TEXT(), nullable=True)
    maximum_rank = database.Column(database.Integer(), nullable=True)
    cooldown = database.Column(database.TEXT(), nullable=True)
    cost = database.Column(database.TEXT(), nullable=True)
    cost_type = database.Column(database.TEXT(), nullable=True)
    maximum_ammo = database.Column(database.TEXT(), nullable=True)
    spell_range = database.Column(database.TEXT(), nullable=True)
    full_image = database.Column(database.TEXT(), nullable=True)
    resource = database.Column(database.TEXT(), nullable=True)
    level = database.Column(database.Integer(), nullable=True)
