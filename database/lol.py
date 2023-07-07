from __future__ import annotations

from database.engine import lol


class Champion(lol.Model):
    __tablename__ = 'champion'

    id = lol.Column(lol.String(10), primary_key=True, nullable=False)
    name = lol.Column(lol.String(50), nullable=True)
    key = lol.Column(lol.String(50), nullable=True)
    title = lol.Column(lol.String(150), nullable=True)
    blurb = lol.Column(lol.Text(), nullable=True)
    attack_information = lol.Column(lol.Integer(), nullable=True)
    defense_information = lol.Column(lol.Integer(), nullable=True)
    magic_information = lol.Column(lol.Integer(), nullable=True)
    difficulty_information = lol.Column(lol.Integer(), nullable=True)
    full_image = lol.Column(lol.String(50), nullable=True)
    champion_class = lol.Column(lol.String(25), nullable=True)
    resource = lol.Column(lol.String(25), nullable=True)
    health = lol.Column(lol.Numeric(), nullable=True)
    health_per_level = lol.Column(lol.Numeric(), nullable=True)
    mana = lol.Column(lol.Numeric(), nullable=True)
    mana_per_level = lol.Column(lol.Numeric(), nullable=True)
    movement_speed = lol.Column(lol.Numeric(), nullable=True)
    armor = lol.Column(lol.Numeric(), nullable=True)
    armor_per_level = lol.Column(lol.Numeric(), nullable=True)
    spellblock = lol.Column(lol.Numeric(), nullable=True)
    spellblock_per_level = lol.Column(lol.Numeric(), nullable=True)
    attack_range = lol.Column(lol.Numeric(), nullable=True)
    health_regeneration = lol.Column(lol.Numeric(), nullable=True)
    health_regeneration_per_level = lol.Column(lol.Numeric(), nullable=True)
    mana_regeneration = lol.Column(lol.Numeric(), nullable=True)
    mana_regeneration_per_level = lol.Column(lol.Numeric(), nullable=True)
    critical_strike = lol.Column(lol.Numeric(), nullable=True)
    critical_strike_per_level = lol.Column(lol.Numeric(), nullable=True)
    attack_damage = lol.Column(lol.Numeric(), nullable=True)
    attack_damage_per_level = lol.Column(lol.Numeric(), nullable=True)
    attack_speed = lol.Column(lol.Numeric(), nullable=True)
    attack_speed_per_level = lol.Column(lol.Numeric(), nullable=True)
    created_at = lol.Column(lol.DateTime(), nullable=True)
    updated_at = lol.Column(lol.DateTime(), nullable=True)


class Ability(lol.Model):
    __tablename__ = 'ability'

    champion_id = lol.Column(lol.String(10), lol.ForeignKey('champion.id'), primary_key=True, nullable=False)

    p_name = lol.Column(lol.String(100), nullable=True)
    p_description = lol.Column(lol.String(1000), nullable=True)
    p_image = lol.Column(lol.String(250), nullable=True)

    q_id = lol.Column(lol.String(100), nullable=True)
    q_name = lol.Column(lol.String(100), nullable=True)
    q_description = lol.Column(lol.String(1000), nullable=True)
    q_image = lol.Column(lol.String(250), nullable=True)

    w_id = lol.Column(lol.String(100), nullable=True)
    w_name = lol.Column(lol.String(100), nullable=True)
    w_description = lol.Column(lol.String(1000), nullable=True)
    w_image = lol.Column(lol.String(250), nullable=True)

    e_id = lol.Column(lol.String(100), nullable=True)
    e_name = lol.Column(lol.String(100), nullable=True)
    e_description = lol.Column(lol.String(1000), nullable=True)
    e_image = lol.Column(lol.String(250), nullable=True)

    r_id = lol.Column(lol.String(100), nullable=True)
    r_name = lol.Column(lol.String(100), nullable=True)
    r_description = lol.Column(lol.String(1000), nullable=True)
    r_image = lol.Column(lol.String(250), nullable=True)

    created_at = lol.Column(lol.DateTime(), nullable=True)
    updated_at = lol.Column(lol.DateTime(), nullable=True)

    _fk_champion_id = lol.ForeignKeyConstraint(['champion_id'], ['champion.id'])


class Item(lol.Model):
    __tablename__ = 'item'

    id = lol.Column(lol.String(10), primary_key=True, nullable=False)
    name = lol.Column(lol.String(150), nullable=True)
    description = lol.Column(lol.Text(), nullable=True)
    ingredients = lol.Column(lol.ARRAY(lol.String()), nullable=True)
    gold_base = lol.Column(lol.Integer(), nullable=True)
    gold_total = lol.Column(lol.Integer(), nullable=True)
    tags = lol.Column(lol.ARRAY(lol.String()), nullable=True)
    full_image = lol.Column(lol.String(25), nullable=True)


class Rune(lol.Model):
    __tablename__ = 'rune'

    id = lol.Column(lol.String(10), primary_key=True, nullable=False)
    key = lol.Column(lol.String(50), nullable=True)
    name = lol.Column(lol.String(50), nullable=True)
    icon = lol.Column(lol.String(250), nullable=True)
    parent = lol.Column(lol.String(10), nullable=True)
    keystone = lol.Column(lol.Boolean(), nullable=True)


class Spell(lol.Model):
    __tablename__ = 'spell'

    id = lol.Column(lol.String(50), primary_key=True, nullable=False)
    key = lol.Column(lol.String(50), nullable=True)
    name = lol.Column(lol.String(50), nullable=True)
    description = lol.Column(lol.Text(), nullable=True)
    maximum_rank = lol.Column(lol.Integer(), nullable=True)
    cooldown = lol.Column(lol.Integer(), nullable=True)
    cost = lol.Column(lol.Integer(), nullable=True)
    cost_type = lol.Column(lol.String(25), nullable=True)
    maximum_ammo = lol.Column(lol.String(5), nullable=True)
    spell_range = lol.Column(lol.Integer(), nullable=True)
    full_image = lol.Column(lol.String(50), nullable=True)
    resource = lol.Column(lol.String(25), nullable=True)
    level = lol.Column(lol.Integer(), nullable=True)


class Version(lol.Model):
    __tablename__ = 'version'

    id = lol.Column(lol.Integer(), primary_key=True, nullable=False)
    item = lol.Column(lol.String(10), nullable=True)
    rune = lol.Column(lol.String(10), nullable=True)
    mastery = lol.Column(lol.String(10), nullable=True)
    summoner = lol.Column(lol.String(10), nullable=True)
    champion = lol.Column(lol.String(10), nullable=True)
    profileicon = lol.Column(lol.String(10), nullable=True)
    map = lol.Column(lol.String(10), nullable=True)
    language = lol.Column(lol.String(10), nullable=True)
    sticker = lol.Column(lol.String(10), nullable=True)


# op.gg

class OPGGNANormal(lol.Model):
    __tablename__ = 'opgg_na_normal'

    champion_id = lol.Column(lol.String(10), lol.ForeignKey('champion.id'), primary_key=True, nullable=False)
    runes = lol.Column(lol.ARRAY(lol.Integer()), nullable=True)
    skills = lol.Column(lol.ARRAY(lol.CHAR(1)), nullable=True)
    items = lol.Column(lol.ARRAY(lol.String()), nullable=True)
    created_at = lol.Column(lol.DateTime(), nullable=True)
    updated_at = lol.Column(lol.DateTime(), nullable=True)

    _fk_champion_id = lol.ForeignKeyConstraint(['champion_id'], ['champion.id'])


class OPGGNAARAM(lol.Model):
    __tablename__ = 'opgg_na_aram'

    champion_id = lol.Column(lol.String(10), lol.ForeignKey('champion.id'), primary_key=True, nullable=False)
    runes = lol.Column(lol.ARRAY(lol.Integer()), nullable=True)
    skills = lol.Column(lol.ARRAY(lol.CHAR(1)), nullable=True)
    items = lol.Column(lol.ARRAY(lol.String()), nullable=True)
    created_at = lol.Column(lol.DateTime(), nullable=True)
    updated_at = lol.Column(lol.DateTime(), nullable=True)

    _fk_champion_id = lol.ForeignKeyConstraint(['champion_id'], ['champion.id'])


class OPGGKRNormal(lol.Model):
    __tablename__ = 'opgg_kr_normal'

    champion_id = lol.Column(lol.String(10), lol.ForeignKey('champion.id'), primary_key=True, nullable=False)
    runes = lol.Column(lol.ARRAY(lol.Integer()), nullable=True)
    skills = lol.Column(lol.ARRAY(lol.CHAR(1)), nullable=True)
    items = lol.Column(lol.ARRAY(lol.String()), nullable=True)
    created_at = lol.Column(lol.DateTime(), nullable=True)
    updated_at = lol.Column(lol.DateTime(), nullable=True)

    _fk_champion_id = lol.ForeignKeyConstraint(['champion_id'], ['champion.id'])


class OPGGKRARAM(lol.Model):
    __tablename__ = 'opgg_kr_aram'

    champion_id = lol.Column(lol.String(10), lol.ForeignKey('champion.id'), primary_key=True, nullable=False)
    runes = lol.Column(lol.ARRAY(lol.Integer()), nullable=True)
    skills = lol.Column(lol.ARRAY(lol.CHAR(1)), nullable=True)
    items = lol.Column(lol.ARRAY(lol.String()), nullable=True)
    created_at = lol.Column(lol.DateTime(), nullable=True)
    updated_at = lol.Column(lol.DateTime(), nullable=True)

    _fk_champion_id = lol.ForeignKeyConstraint(['champion_id'], ['champion.id'])
