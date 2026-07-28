from __future__ import annotations

import msgspec


class Summoner(msgspec.Struct):
    identifier: str | None = msgspec.field(default=None, name='id')
    level: int | None = msgspec.field(default=None, name='summonerLevel')
    name: str | None = msgspec.field(default=None, name='riotId')
    puuid: str | None = None


class Participant(msgspec.Struct):
    champion: int | None = msgspec.field(default=None, name='championId')
    name: str | None = msgspec.field(default=None, name='riotId')
    puuid: str | None = None
    team: int | None = msgspec.field(default=None, name='teamId')


class Game(msgspec.Struct):
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

    identifier: int | None = msgspec.field(default=None, name='gameId')
    map: int | None = msgspec.field(default=None, name='mapId')
    participants: list[Participant] = []
    queue: int | None = msgspec.field(default=None, name='gameQueueConfigId')
    type: str | None = msgspec.field(default=None, name='gameType')

    @property
    def mode(self) -> str | None:
        return self.QUEUES.get(self.queue)


class League(msgspec.Struct):
    QUEUES = {
        'RANKED_SOLO_5x5': 'Solo Queue (5v5)',
        'RANKED_FLEX_SR': 'Flex Queue (5x5)',
        'RANKED_FLEX_TT': 'Flex Queue (3x3)',
        'RANKED_TFT_DOUBLE_UP': 'Teamfight Tactics (Double Up)',
    }

    losses: int | None = None
    name: str | None = msgspec.field(default=None, name='leagueName')
    points: int | None = msgspec.field(default=None, name='leaguePoints')
    queue: str | None = msgspec.field(default=None, name='queueType')
    rank: str | None = None
    tier: str | None = None
    wins: int | None = None

    @property
    def queues(self) -> str | None:
        return self.QUEUES.get(self.queue)

    @property
    def standing(self) -> str:
        if self.tier is None:
            return f'[{self.points} LP] [{round(self.win_loss)}%]'

        return f'{self.tier.title()} {self.rank} [{self.points} LP] [{round(self.win_loss)}%]'

    @property
    def win_loss(self) -> float:
        wins = self.wins or 0
        losses = self.losses or 0
        total = wins + losses

        if total == 0:
            return 0.0

        return (wins / total) * 100


class Mastery(msgspec.Struct):
    identifier: int | None = msgspec.field(default=None, name='championId')
    level: int | None = msgspec.field(default=None, name='championLevel')
    points: int | None = msgspec.field(default=None, name='championPoints')

    @property
    def summary(self) -> str:
        if self.points is None:
            points = 'Unknown'
        else:
            points = f'{self.points:,}'

        return f'Level {self.level} [{points} Points]'
