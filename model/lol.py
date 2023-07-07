from __future__ import annotations

from dataclasses import dataclass


@dataclass
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
    def mode(self) -> str | None:
        if self.queue in self.QUEUES:
            return self.QUEUES[self.queue]

        return None


@dataclass
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
        'RANKED_FLEX_TT': 'Flex Queue (3x3)',
        'RANKED_TFT_DOUBLE_UP': 'Teamfight Tactics (Double Up)',
    }

    def __init__(self, data):
        self.name = data.get('leagueName')
        self.queue = data.get('queueType')

        if data.get('tier'):
            self.tier = data.get('tier').title()

        if data.get('rank'):
            self.rank = data.get('rank')

        self.wins = data.get('wins')
        self.losses = data.get('losses')
        self.points = data.get('leaguePoints')

    def __repr__(self):
        if self.queue == 'RANKED_TFT_PAIRS':
            return f"[{self.points} LP] [{round(self.win_loss)}%]"
        else:
            return f"{self.tier} {self.rank} [{self.points} LP] [{round(self.win_loss)}%]"

    @property
    def win_loss(self):
        return (self.wins / (self.wins + self.losses)) * 100

    @property
    def queues(self):
        if self.queue in self.QUEUES:
            return self.QUEUES[self.queue]


@dataclass
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


@dataclass
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


@dataclass
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
