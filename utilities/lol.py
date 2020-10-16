from database.model import LoLChampions, LoLSpells
from rapidfuzz import process
from utilities.format import format_list
from utilities.request import fetch


BASE = 'https://na1.api.riotgames.com/lol'
ASSET = 'https://ddragon.leagueoflegends.com'
UGG = 'https://u.gg/lol/champions'


class Summoner:
    __slots__ = (
        'id',
        'name',
        'level'
    )

    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.level = data.get('summonerLevel')


class League:
    __slots__ = (
        'name',
        'queue',
        'tier',
        'rank',
        'wins',
        'losses',
        'points'
    )

    QUEUES = {
        'RANKED_SOLO_5x5': 'Solo Queue (5v5)',
        'RANKED_FLEX_SR': 'Flex Queue (5x5)',
        'RANKED_FLEX_TT': 'Flex Queue (3x3)'
    }

    def __init__(self, data):
        self.name = data.get('leagueName')
        self.queue = data.get('queueType')
        self.tier = data.get('tier').title()
        self.rank = data.get('rank')
        self.wins = data.get('wins')
        self.losses = data.get('losses')
        self.points = data.get('leaguePoints')

    def __repr__(self):
        return f"{self.tier} {self.rank} [{self.points} LP] [{round(self.win_loss)}%]"

    @property
    def win_loss(self):
        return (self.wins / (self.wins + self.losses)) * 100

    @property
    def queues(self):
        if self.queue in self.QUEUES:
            return self.QUEUES[self.queue]


class Mastery:
    __slots__ = (
        'id',
        'level',
        'points'
    )

    def __init__(self, data):
        self.id = data.get('championId')
        self.level = data.get('championLevel')
        self.points = data.get('championPoints')

    def __repr__(self):
        return f"Level {self.level} [{self.points:,} Points]"


class Game:
    __slots__ = (
        'id',
        'map',
        'type',
        'queue',
        'participants'
    )

    QUEUES = {
        0: 'Custom Game',
        72: 'Howling Abyss - Snowdown Showdown (1v1)',
        73: 'Howling Abyss - Snowdown Showdown (2v2)',
        75: 'Summoner\'s Rift - Hexakill (6v6)',
        76: 'Summoner\'s Rift - Ultra Rapid Fire',
        78: 'Howling Abyss - One For All: Mirror Mode',
        83: 'Summoner\'s Rift - Ultra Rapid Fire (Co-op vs AI)',
        98: 'Twisted Treeline - Hexakill (6v6)',
        100: 'Butcher\'s Bridge - ARAM (5v5)',
        310: 'Summoner\'s Rift - Nemesis',
        313: 'Summoner\'s Rift - Black Market Brawlers',
        317: 'Crystal Scar - Definitely Not Dominion',
        325: 'Summoner\'s Rift - All Random',
        400: 'Summoner\'s Rift - Draft Pick (5v5)',
        420: 'Summoner\'s Rift - Ranked Solo (5v5)',
        430: 'Summoner\'s Rift - Blind Pick (5v5)',
        440: 'Summoner\'s Rift - Ranked Flex (5v5)',
        450: 'Howling Abyss - ARAM (5v5)',
        460: 'Twisted Treeline - Blind Pick (3v3)',
        470: 'Twisted Treeline - Ranked Flex (3v3)',
        600: 'Summoner\'s Rift - Blood Hunt Assassin',
        610: 'Cosmic Ruins - Dark Star: Singularity',
        700: 'Summoner\'s Rift - Clash',
        800: 'Twisted Treeline - Intermediate Bot (Co-op vs AI)',
        810: 'Twisted Treeline - Intro Bot (Co-op vs AI)',
        820: 'Twisted Treeline - Beginner Bot (Co-op vs AI)',
        830: 'Summoner\'s Rift - Intro Bot (Co-op vs AI)',
        840: 'Summoner\'s Rift - Beginner Bot (Co-op vs AI)',
        850: 'Summoner\'s Rift - Intermediate Bot (Co-op vs AI)',
        900: 'Summoner\'s Rift - ARURF',
        910: 'Crystal Scar - Ascension',
        920: 'Howling Abyss - Legend of the Poro King',
        940: 'Summoner\'s Rift - Nexus Siege',
        950: 'Summoner\'s Rift - Doom Bots (Voting)',
        960: 'Summoner\'s Rift - Doom Bots (Standard)',
        980: 'Valoran City Park - Star Guardian Invasion: Normal',
        990: 'Valoran City Park - Star Guardian Invasion: Onslaught',
        1000: 'Overcharge - PROJECT: Hunters',
        1010: 'Summoner\'s Rift - Snow ARURF',
        1020: 'Summoner\'s Rift - One for All',
        1030: 'Crash Site - Odyssey Extraction: Intro',
        1040: 'Crash Site - Odyssey Extraction: Cadet',
        1050: 'Crash Site - Odyssey Extraction: Crewmember',
        1060: 'Crash Site - Odyssey Extraction: Captain',
        1070: 'Crash Site - Odyssey Extraction: Onslaught'
    }

    def __init__(self, data):
        self.id = data.get('gameId')
        self.map = data.get('mapId')
        self.type = data.get('gameType')
        self.queue = data.get('gameQueueConfigId')
        self.participants = data.get('participants')

    @property
    def mode(self):
        if self.queue in self.QUEUES:
            return self.QUEUES[self.queue]


class Participants:
    __slots__ = (
        'id',
        'name',
        'team',
        'champion'
    )

    def __init__(self, data):
        self.id = data.get('summonerId')
        self.name = data.get('summonerName')
        self.team = data.get('teamId')
        self.champion = data.get('championId')


class Champion:
    __slots__ = (
        'id',
        'key',
        'name',
        'title',
        'blurb',
        'attack_information',
        'defense_information',
        'magic_information',
        'difficulty_information',
        'full_image',
        'champion_class',
        'resource',
        'health',
        'health_per_level',
        'mana',
        'mana_per_level',
        'movement_speed',
        'armor',
        'armor_per_level',
        'spellblock',
        'spellblock_per_level',
        'attack_range',
        'health_regeneration',
        'health_regeneration_per_level',
        'mana_regeneration',
        'mana_regeneration_per_level',
        'critical_strike',
        'critical_strike_per_level',
        'attack_damage',
        'attack_damage_per_level',
        'attack_speed_per_level',
        'attack_speed'
    )

    def __init__(self, data):
        self.id = data.get('id')
        self.key = data.get('key')
        self.name = data.get('name')
        self.title = data.get('title')
        self.blurb = data.get('blurb')
        self.attack_information = data.get('info').get('attack')
        self.defense_information = data.get('info').get('defense')
        self.magic_information = data.get('info').get('magic')
        self.difficulty_information = data.get('info').get('difficulty')
        self.full_image = data.get('image').get('full')
        self.champion_class = data.get('tags')[0]
        self.resource = data.get('partype')
        self.health = data.get('stats').get('hp')
        self.health_per_level = data.get('stats').get('hpperlevel')
        self.mana = data.get('stats').get('mp')
        self.mana_per_level = data.get('stats').get('mpperlevel')
        self.movement_speed = data.get('stats').get('movespeed')
        self.armor = data.get('stats').get('armor')
        self.armor_per_level = data.get('stats').get('armorperlevel')
        self.spellblock = data.get('stats').get('spellblock')
        self.spellblock_per_level = data.get('stats').get('spellblockperlevel')
        self.attack_range = data.get('stats').get('attackrange')
        self.health_regeneration = data.get('stats').get('hpregen')
        self.health_regeneration_per_level = data.get('stats').get('hpregenperlevel')
        self.mana_regeneration = data.get('stats').get('mpregen')
        self.mana_regeneration_per_level = data.get('stats').get('mpregenperlevel')
        self.critical_strike = data.get('stats').get('crit')
        self.critical_strike_per_level = data.get('stats').get('critperlevel')
        self.attack_damage = data.get('stats').get('attackdamage')
        self.attack_damage_per_level = data.get('stats').get('attackdamageperlevel')
        self.attack_speed_per_level = data.get('stats').get('attackspeedperlevel')
        self.attack_speed = data.get('stats').get('attackspeed')


class Spell:
    __slots__ = (
        'id',
        'name',
        'description',
        'maximum_rank',
        'cooldown',
        'cost',
        'cost_type',
        'maximum_ammo',
        'spell_range',
        'key',
        'full_image',
        'resource',
        'level'
    )

    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.description = data.get('description')
        self.maximum_rank = data.get('maxrank')
        self.cooldown = data.get('cooldownBurn')
        self.cost = data.get('costBurn')
        self.cost_type = data.get('costType')
        self.maximum_ammo = data.get('maxammo')
        self.spell_range = data.get('rangeBurn')
        self.key = data.get('key')
        self.full_image = data.get('image').get('full')
        self.resource = data.get('resource')
        self.level = data.get('summonerLevel')


async def get_current_version(session):
    url = f"{ASSET}/realms/na.json"
    response = await fetch(session, url)
    return response.get('n')


async def get_champion_version(session):
    version = await get_current_version(session)
    return version.get('champion')


async def get_spell_version(session):
    version = await get_current_version(session)
    return version.get('summoner')


async def get_champions(session, version: str):
    url = f"{ASSET}/cdn/{version}/data/en_US/champion.json"
    return await fetch(session, url)


async def get_spells(session, version: str):
    url = f"{ASSET}/cdn/{version}/data/en_US/summoner.json"
    return await fetch(session, url)


async def get_champion_masteries(session, params, summoner_id: int):
    url = f"{BASE}/champion-mastery/v4/champion-masteries/by-summoner/{summoner_id}"
    return await fetch(session, url, params=params)


async def get_summoner_account(session, params, summoner_name: str):
    url = f"{BASE}/summoner/v4/summoners/by-name/{summoner_name}"
    return await fetch(session, url, params=params)


async def get_summoner_leagues(session, params, summoner_id: int):
    url = f"{BASE}/league/v4/entries/by-summoner/{summoner_id}"
    return await fetch(session, url, params=params)


async def get_active_game(session, params, summoner_name: str):
    summoner = await get_summoner_account(session, params, summoner_name)
    summoner_id = summoner.get('id')

    url = f"{BASE}/spectator/v4/active-games/by-summoner/{summoner_id}"
    return await fetch(session, url, params=params)


async def get_champion_name(champion_id: int):
    champion = (
        await LoLChampions
        .select('name')
        .where(
            LoLChampions.champion_id == str(champion_id)
        )
        .gino
        .first()
    )

    return dict(champion).get('name')


async def get_champion_names():
    champions = await LoLChampions.select('name').gino.all()
    return [dict(champion).get('name') for champion in champions]


async def get_spell_names():
    spells = await LoLSpells.select('name').gino.all()
    return [dict(spell).get('name') for spell in spells]


async def get_champion_statistics(champion_name: str):
    return (
        await LoLChampions
        .query
        .where(LoLChampions.name == champion_name)
        .gino
        .first()
    )


async def get_spell_statistics(spell_name: str):
    return (
        await LoLSpells
        .query
        .where(LoLSpells.name == spell_name)
        .gino
        .first()
    )


async def search_for_champion(champion_name: str):
    champion_names = await get_champion_names()

    match, score = process.extractOne(
        champion_name,
        champion_names
    )

    return match


async def search_for_spell(spell_name: str):
    spell_names = await get_spell_names()

    match, score = process.extractOne(
        spell_name,
        spell_names
    )

    return match


async def get_placement(leagues):
    placement = ''

    display = {
        'RANKED_SOLO_5x5': 1,
        'RANKED_FLEX_SR': 2,
        'RANKED_FLEX_TT': 3,
        'RANKED_TFT': 4
    }

    leagues.sort(
        key=lambda orderly: display[
            orderly['queueType']
        ]
    )

    for league in leagues:
        queue = League(league)
        placement += f"{queue.queues}: {queue} \n"

    if not placement:
        placement += 'Unranked'

    return placement


async def get_mastery(session, params, summoner_id: int):
    get_masteries = await get_champion_masteries(
        session,
        params,
        summoner_id
    )

    champions = []

    for masteries in get_masteries[:10]:
        mastery = Mastery(masteries)
        name = await get_champion_name(mastery.id)
        champions.append(
            f"{name}: {mastery}"
        )

    return format_list(champions, sort=False)
