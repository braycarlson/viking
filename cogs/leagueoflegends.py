import asyncio
import discord
import json
import logging
import os
from discord.ext import commands
from fuzzywuzzy import process
from typing import Dict, List, Union
from utilities.checks import is_channel
from utilities.format import alpha, format_list
from utilities.redis import Redis
from utilities.request import download, fetch, RequestError
from utilities.time import midnight


log = logging.getLogger(__name__)

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
        'RANKED_FLEX_TT': 'Flex Queue (3x3)',
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
        'name',
        'avatar',
        'health',
        'health_per_level',
        'mana',
        'mana_per_level',
        'movement_speed',
        'attack_range',
        'attack_damage',
        'attack_damage_per_level',
        'attack_speed',
        'attack_speed_per_level',
        'critical_strike',
        'critical_strike_per_level',
        'health_regeneration',
        'health_regeneration_per_level',
        'armor',
        'armor_per_level',
        'mana_regeneration',
        'mana_regeneration_per_level',
        'version'
    )

    def __init__(self, data):
        self.name = data.get('name')
        self.avatar = data.get('image').get('full')
        self.health = data.get('stats').get('hp')
        self.health_per_level = data.get('stats').get('hpperlevel')
        self.mana = data.get('stats').get('mp')
        self.mana_per_level = data.get('stats').get('mpperlevel')
        self.movement_speed = data.get('stats').get('movespeed')
        self.attack_range = data.get('stats').get('attackrange')
        self.attack_damage = data.get('stats').get('attackdamage')
        self.attack_damage_per_level = data.get('stats').get('attackdamageperlevel')
        self.attack_speed = data.get('stats').get('attackspeed')
        self.attack_speed_per_level = data.get('stats').get('attackspeedperlevel')
        self.critical_strike = data.get('stats').get('crit')
        self.critical_strike_per_level = data.get('stats').get('critperlevel')
        self.health_regeneration = data.get('stats').get('hpregen')
        self.health_regeneration_per_level = data.get('stats').get('hpregenperlevel')
        self.armor = data.get('stats').get('armor')
        self.armor_per_level = data.get('stats').get('armorperlevel')
        self.mana_regeneration = data.get('stats').get('mpregen')
        self.mana_regeneration_per_level = data.get('stats').get('mpregenperlevel')
        self.version = data.get('version')

    @property
    def image(self):
        return f"{ASSET}/cdn/{self.version}/img/champion/{self.avatar}"


class Spell:
    __slots__ = (
        'match',
        'score',
        'id',
        'spell',
        'avatar',
        'name',
        'description',
        'range',
        'cooldown',
        'key',
        'level',
        'version'
    )

    SPELLS = {
        'barrier': 'SummonerBarrier',
        'cleanse': 'SummonerBoost',
        'ignite': 'SummonerDot',
        'exhaust': 'SummonerExhaust',
        'flash': 'SummonerFlash',
        'ghost': 'SummonerHaste',
        'heal': 'SummonerHeal',
        'clarity': 'SummonerMana',
        'warp': 'SummonerOdysseyFlash',
        'revive': 'SummonerOdysseyRevive',
        'to the king': 'SummonerPoroRecall',
        'poro toss': 'SummonerPoroThrow',
        'smite': 'SummonerSmite',
        'ultra mark': 'SummonerSnowURFSnowball_Mark',
        'mark': 'SummonerSnowball',
        'teleport': 'SummonerTeleport',
    }

    def __init__(self, data, spell: str):
        self.match, self.score = process.extractOne(
            spell,
            self.SPELLS.keys()
        )

        self.spell = self.SPELLS.get(self.match)
        self.id = data.get('data').get(self.spell).get('id')
        self.avatar = data.get('data').get(self.spell).get('image').get('full')
        self.name = data.get('data').get(self.spell).get('name')
        self.description = data.get('data').get(self.spell).get('description')
        self.range = data.get('data').get(self.spell).get('rangeBurn')
        self.cooldown = data.get('data').get(self.spell).get('cooldownBurn')
        self.key = data.get('data').get(self.spell).get('key')
        self.level = data.get('data').get(self.spell).get('summonerLevel')
        self.version = data.get('version')

    @property
    def image(self):
        return f"{ASSET}/cdn/{self.version}/img/spell/{self.avatar}"


class LeagueOfLegends(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.champion_path = os.path.join(
            self.viking.root,
            'downloads/champions.json'
        )
        self.lol_api_key = viking.lol_api_key
        self.params = {'api_key': self.lol_api_key}
        self.redis = Redis(self.viking)
        self.session = viking.session
        self.spell_path = os.path.join(
            self.viking.root,
            'downloads/spells.json'
        )
        self.viking.loop.create_task(
            self.check_champion_version()
        )
        self.viking.loop.create_task(
            self.check_spell_version()
        )

    @commands.Cog.listener()
    async def on_connect(self):
        """
        An event that is called when the client has successfully
        connected to Discord.
        """

        if not os.path.exists(self.champion_path):
            await self.update_champion_version()

        if not os.path.exists(self.spell_path):
            await self.update_spell_version()

    async def get_current_version(self) -> Dict[str, str]:
        url = f"{ASSET}/realms/na.json"
        response = await fetch(self.session, url)
        return response.get('n')

    async def get_champion_version(self) -> str:
        version = await self.get_current_version()
        return version.get('champion')

    async def get_spell_version(self) -> str:
        version = await self.get_current_version()
        return version.get('summoner')

    async def check_champion_version(self):
        time = midnight()
        await asyncio.sleep(time)

        cache = await self.redis.get('champion_version')
        current = await self.get_champion_version()

        if cache != current or not os.path.exists(self.champion_path):
            await self.update_champion_version(current)

    async def check_spell_version(self):
        time = midnight()
        await asyncio.sleep(time)

        cache = await self.redis.get('spell_version')
        current = await self.get_spell_version()

        if cache != current or not os.path.exists(self.spell_path):
            await self.update_spell_version(current)

    async def update_champion_version(self, current=None):
        if current is None:
            version = await self.get_current_version()
            current = version.get('champion')

        await self.download_champions(current)
        await self.redis.set('champion_version', current)

    async def update_spell_version(self, current=None):
        if current is None:
            version = await self.get_current_version()
            current = version.get('summoner')

        await self.download_spells(current)
        await self.redis.set('spell_version', current)

    async def download_champions(self, version: str):
        url = f"{ASSET}/cdn/{version}/data/en_US/champion.json"
        await download(self.session, url, self.champion_path)

    async def download_spells(self, version: str):
        url = f"{ASSET}/cdn/{version}/data/en_US/summoner.json"
        await download(self.session, url, self.spell_path)

    async def get_champion_masteries(
        self,
        summoner_id: int
    ) -> List[Dict[str, Union[str, int]]]:
        url = f"{BASE}/champion-mastery/v4/champion-masteries/by-summoner/{summoner_id}"
        return await fetch(self.session, url, params=self.params)

    async def get_summoner_account(
        self,
        summoner_name: str
    ) -> Dict[str, Union[str, int]]:
        url = f"{BASE}/summoner/v4/summoners/by-name/{summoner_name}"
        return await fetch(self.session, url, params=self.params)

    async def get_summoner_leagues(
        self,
        summoner_id: int
    ) -> List[Dict[str, Union[str, int]]]:
        url = f"{BASE}/league/v4/entries/by-summoner/{summoner_id}"
        return await fetch(self.session, url, params=self.params)

    async def get_active_game(
        self,
        summoner_name: str
    ) -> Dict[str, Union[str, int]]:
        summoner = await self.get_summoner_account(summoner_name)
        summoner_id = summoner.get('id')

        url = f"{BASE}/spectator/v4/active-games/by-summoner/{summoner_id}"
        return await fetch(self.session, url, params=self.params)

    async def get_champion_name(self, champion_id: int) -> str:
        with open(self.champion_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

            for champion in data.get('data').values():
                if str(champion_id) == champion.get('key'):
                    return champion.get('name')

    async def get_champion_names(self) -> List[str]:
        with open(self.champion_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

            return [
                champion.get('name')
                for champion in data.get('data').values()
            ]

    async def get_champion_statistics(
        self,
        champion_name: str
    ) -> Dict[str, Union[str, int]]:
        with open(self.champion_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

            for champion in data.get('data').values():
                if champion_name == champion.get('name'):
                    return champion

    async def search_for_champion(self, champion_name: str) -> str:
        champion_names = await self.get_champion_names()

        match, score = process.extractOne(
            champion_name,
            champion_names
        )

        return match

    async def placement(
        self,
        leagues: List[Dict[str, Union[str, int]]]
    ) -> str:
        placement = ''

        display = {
            'RANKED_SOLO_5x5': 1,
            'RANKED_FLEX_SR': 2,
            'RANKED_FLEX_TT': 3
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

    async def mastery(self, summoner_id: int) -> str:
        get_masteries = await self.get_champion_masteries(summoner_id)

        champions = []

        for masteries in get_masteries[:10]:
            mastery = Mastery(masteries)
            name = await self.get_champion_name(mastery.id)
            champions.append(
                f"{name}: {mastery}"
            )

        return format_list(champions, sort=False)

    @commands.command()
    @is_channel(579830092352716820)
    async def build(self, ctx, *, champion_name: str):
        """
        *build <name>

        A command that links you to a champion's most frequent and
        highest winning build path.
        """

        name = alpha(champion_name)
        result = await self.search_for_champion(name)
        champion = alpha(result)

        await ctx.send(f"{UGG}/{champion}/build?rank=diamond_plus")

    @commands.command()
    @is_channel(579830092352716820)
    async def counters(self, ctx, *, champion_name: str):
        """
        *counters <name>

        A command that links you to a champion's counters
        """

        name = alpha(champion_name)
        result = await self.search_for_champion(name)
        champion = alpha(result)

        await ctx.send(f"{UGG}/{champion}/counters?rank=diamond_plus")

    @commands.command()
    @is_channel(579830092352716820)
    async def champion(self, ctx, *, champion_name: str):
        """
        *champion <name>

        A command that displays a champion's statistics
        """

        async with ctx.typing():
            name = await self.search_for_champion(champion_name)
            get_champion = await self.get_champion_statistics(name)
            champion = Champion(get_champion)

            embed = discord.Embed(
                inline=False,
                colour=self.viking.color,
                title=champion.name
            )
            embed.set_thumbnail(
                url=champion.image
            )
            embed.add_field(
                name='Health',
                value=f"{champion.health} "
                      f"(+{champion.health_per_level} per level)"
            )
            embed.add_field(
                name='Health Regeneration',
                value=f"{champion.health_regeneration} "
                      f"(+{champion.health_regeneration_per_level} per level)"
            )
            embed.add_field(
                name='Mana',
                value=f"{champion.mana} "
                      f"(+{champion.mana_per_level} per level)"
            )
            embed.add_field(
                name='Mana Regeneration',
                value=f"{champion.mana_regeneration} "
                      f"(+{champion.mana_regeneration_per_level} per level)"
            )
            embed.add_field(
                name='Armor',
                value=f"{champion.armor} "
                      f"(+{champion.armor_per_level} per level)"
            )
            embed.add_field(
                name='Movement Speed',
                value=champion.movement_speed
            )
            embed.add_field(
                name='Attack Range',
                value=champion.attack_range
            )
            embed.add_field(
                name='Attack Damage',
                value=f"{champion.attack_damage} "
                      f"(+{champion.attack_damage_per_level} per level)"
            )
            embed.add_field(
                name='Attack Speed',
                value=f"{champion.attack_speed} "
                      f"(+{champion.attack_speed_per_level} per level)"
            )
            embed.add_field(
                name='Critical Strike',
                value=f"{champion.critical_strike} "
                      f"(+{champion.critical_strike_per_level} per level)"
            )

        await ctx.send(embed=embed)

    @commands.command()
    @is_channel(579830092352716820)
    async def duo(self, ctx, *, champion_name: str):
        """
        *duo <name>

        A command that links you to a champion's most successful duo.
        """

        name = alpha(champion_name)
        result = await self.search_for_champion(name)
        champion = alpha(result)

        await ctx.send(f"{UGG}/{champion}/duos?rank=diamond_plus")

    @commands.command(aliases=['live'])
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.default)
    @is_channel(579830092352716820)
    async def game(self, ctx, *, summoner_name: str):
        """
        *game <username>

        A command that display an overview of everyone in an active
        game including: name, level, champion, rank and win/loss ratio.
        """

        try:
            get_game = await self.get_active_game(summoner_name)
        except RequestError:
            await ctx.send('No game or summoner found.')
        else:
            async with ctx.typing():
                game = Game(get_game)

                main = discord.Embed(
                    title='Game',
                    description=f"{game.mode}"
                )
                blue = discord.Embed(
                    title='Blue Team',
                    colour=discord.Colour.blue()
                )
                red = discord.Embed(
                    title='Red Team',
                    colour=discord.Colour.red()
                )

                for participant in game.participants:
                    participant = Participants(participant)
                    leagues = await self.get_summoner_leagues(participant.id)
                    placement = await self.placement(leagues)
                    champion = await self.get_champion_name(participant.champion)

                    if participant.team == 100:
                        blue.add_field(
                            inline=False,
                            name=f"{champion} ({participant.name})",
                            value=placement
                        )

                    if participant.team == 200:
                        red.add_field(
                            inline=False,
                            name=f"{champion} ({participant.name})",
                            value=placement
                        )

            await ctx.send(embed=main)
            await ctx.send(embed=blue)
            await ctx.send(embed=red)

    @commands.command()
    @is_channel(579830092352716820)
    async def matchups(self, ctx, *, champion_name: str):
        """
        *matchups <name>

        A command that links you to a champion's most successful
        matchups in descending order.
        """

        name = alpha(champion_name)
        result = await self.search_for_champion(name)
        champion = alpha(result)

        await ctx.send(f"{UGG}/{champion}/matchups?rank=diamond_plus")

    @commands.command()
    @is_channel(579830092352716820)
    async def path(self, ctx, *, champion_name: str):
        """
        *path <name>

        A command that links you to a champion's most successful
        build path in descending order.
        """

        name = alpha(champion_name)
        result = await self.search_for_champion(name)
        champion = alpha(result)

        await ctx.send(f"{UGG}/{champion}/item-paths?rank=diamond_plus")

    @commands.command()
    @is_channel(579830092352716820)
    async def probuild(self, ctx, *, champion_name: str):
        """
        *probuild <name>

        A command that links you to a professional player's game,
        and show you how they played the champion.
        """

        name = alpha(champion_name)
        result = await self.search_for_champion(name)
        champion = alpha(result)

        await ctx.send(f"{UGG}/{champion}/pro-build?region=kr")

    @commands.command()
    @is_channel(579830092352716820)
    async def runes(self, ctx, *, champion_name: str):
        """
        *runes <name>

        A command that links you to a champion's most successful
        rune page in descending order.
        """

        name = alpha(champion_name)
        result = await self.search_for_champion(name)
        champion = alpha(result)

        await ctx.send(f"{UGG}/{champion}/rune-sets?rank=diamond_plus")

    @commands.command()
    @is_channel(579830092352716820)
    async def spell(self, ctx, *, name: str):
        """
        *spell <name>

        A command that displays a summoner spell's statistics.
        """

        async with ctx.typing():
            with open(self.spell_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

                spell = Spell(data, name)

                embed = discord.Embed(
                    colour=self.viking.color
                )
                embed.set_thumbnail(
                    url=spell.image
                )
                embed.add_field(
                    inline=False,
                    name='Name',
                    value=spell.name
                )
                embed.add_field(
                    inline=False,
                    name='Description',
                    value=spell.description
                )
                embed.add_field(
                    inline=False,
                    name='Acquired',
                    value=f"Level {spell.level}"
                )
                embed.add_field(
                    inline=False,
                    name='Range',
                    value=f"{spell.range} units"
                )
                embed.add_field(
                    inline=False,
                    name='Cooldown',
                    value=f"{spell.cooldown} seconds"
                )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.default)
    @is_channel(579830092352716820)
    async def summoner(self, ctx, *, summoner_name: str):
        """
        *summoner <username>

        A command that provides you with information regarding a
        League of Legends account including: name, level, rank, points,
        win/loss ratio, and the top five champions with the highest
        mastery points.
        """

        try:
            get_summoner = await self.get_summoner_account(summoner_name)
        except RequestError:
            await ctx.send('No summoner found.')
        else:
            async with ctx.typing():
                summoner = Summoner(get_summoner)
                leagues = await self.get_summoner_leagues(summoner.id)
                placement = await self.placement(leagues)
                champions = await self.mastery(summoner.id)

                embed = discord.Embed(
                    title=f"{summoner.name} (Level {summoner.level})",
                    colour=self.viking.color
                )

                embed.add_field(
                    inline=False,
                    name='Placement',
                    value=placement
                )

                embed.add_field(
                    inline=False,
                    name='Champions',
                    value=champions
                )

            await ctx.send(embed=embed)


def setup(viking):
    viking.add_cog(LeagueOfLegends(viking))
