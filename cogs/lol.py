import discord
import logging
from discord.ext import commands
from utilities.format import alphabet
from utilities.lol import (
    ASSET,
    Game,
    Participants,
    Summoner,
    get_active_game,
    get_summoner_account,
    get_summoner_leagues,
    get_champion_name,
    get_champion_names,
    get_champion_statistics,
    get_champion_version,
    get_spell_statistics,
    get_spell_version,
    get_mastery,
    get_placement,
    search_for_champion,
    search_for_spell,
    UGG
)
from utilities.request import RequestError


log = logging.getLogger(__name__)


class LeagueOfLegends(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.lol_api_key = viking.lol_api_key
        self.params = {'api_key': self.lol_api_key}
        self.session = viking.session

    @commands.command()
    async def build(self, ctx, *, champion_name: str):
        """
        *build <name>

        A command that links you to a champion's most frequent and
        highest winning build path.
        """

        name = alphabet(champion_name)
        result = await search_for_champion(name)
        champion = alphabet(result)

        await ctx.send(f"{UGG}/{champion}/build?rank=diamond_plus")

    @commands.command()
    async def counters(self, ctx, *, champion_name: str):
        """
        *counters <name>

        A command that links you to a champion's counters
        """

        name = alphabet(champion_name)
        result = await search_for_champion(name)
        champion = alphabet(result)

        await ctx.send(f"{UGG}/{champion}/counters?rank=diamond_plus")

    @commands.command()
    async def champion(self, ctx, *, champion_name: str):
        """
        *champion <name>

        A command that displays a champion's statistics
        """

        async with ctx.typing():
            name = await search_for_champion(champion_name)
            champion = await get_champion_statistics(name)
            version = await get_champion_version(self.session)

            embed = discord.Embed(
                inline=False,
                colour=self.viking.color,
                title=champion.name
            )
            embed.set_thumbnail(
                url=f"{ASSET}/cdn/{version}/img/champion/{champion.full_image}"
            )
            embed.add_field(
                inline=False,
                name='Health',
                value=f"{champion.health} "
                      f"(+{champion.health_per_level} per level)"
            )
            embed.add_field(
                inline=False,
                name='Health Regeneration',
                value=f"{champion.health_regeneration} "
                      f"(+{champion.health_regeneration_per_level} per level)"
            )
            embed.add_field(
                inline=False,
                name='Mana',
                value=f"{champion.mana} "
                      f"(+{champion.mana_per_level} per level)"
            )
            embed.add_field(
                inline=False,
                name='Mana Regeneration',
                value=f"{champion.mana_regeneration} "
                      f"(+{champion.mana_regeneration_per_level} per level)"
            )
            embed.add_field(
                inline=False,
                name='Armor',
                value=f"{champion.armor} "
                      f"(+{champion.armor_per_level} per level)"
            )
            embed.add_field(
                inline=False,
                name='Movement Speed',
                value=champion.movement_speed
            )
            embed.add_field(
                inline=False,
                name='Attack Range',
                value=champion.attack_range
            )
            embed.add_field(
                inline=False,
                name='Attack Damage',
                value=f"{champion.attack_damage} "
                      f"(+{champion.attack_damage_per_level} per level)"
            )
            embed.add_field(
                inline=False,
                name='Attack Speed',
                value=f"{champion.attack_speed} "
                      f"(+{champion.attack_speed_per_level} per level)"
            )
            embed.add_field(
                inline=False,
                name='Critical Strike',
                value=f"{champion.critical_strike} "
                      f"(+{champion.critical_strike_per_level} per level)"
            )

        await ctx.send(embed=embed)

    @commands.command()
    async def duo(self, ctx, *, champion_name: str):
        """
        *duo <name>

        A command that links you to a champion's most successful duo.
        """

        name = alphabet(champion_name)
        result = await search_for_champion(name)
        champion = alphabet(result)

        await ctx.send(f"{UGG}/{champion}/duos?rank=diamond_plus")

    @commands.command(aliases=['live'])
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.default)
    async def game(self, ctx, *, summoner_name: str):
        """
        *game <username>

        A command that display an overview of everyone in an active
        game including: name, level, champion, rank and win/loss ratio.
        """

        try:
            get_game = await get_active_game(
                self.session,
                self.params,
                summoner_name
            )
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
                    leagues = await get_summoner_leagues(
                        self.session,
                        self.params,
                        participant.id
                    )
                    placement = await get_placement(leagues)
                    champion = await get_champion_name(participant.champion)

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
    async def matchups(self, ctx, *, champion_name: str):
        """
        *matchups <name>

        A command that links you to a champion's most successful
        matchups in descending order.
        """

        name = alphabet(champion_name)
        result = await search_for_champion(name)
        champion = alphabet(result)

        await ctx.send(f"{UGG}/{champion}/matchups?rank=diamond_plus")

    @commands.command()
    async def path(self, ctx, *, champion_name: str):
        """
        *path <name>

        A command that links you to a champion's most successful
        build path in descending order.
        """

        name = alphabet(champion_name)
        result = await search_for_champion(name)
        champion = alphabet(result)

        await ctx.send(f"{UGG}/{champion}/item-paths?rank=diamond_plus")

    @commands.command()
    async def probuild(self, ctx, *, champion_name: str):
        """
        *probuild <name>

        A command that links you to a professional player's game,
        and show you how they played the champion.
        """

        name = alphabet(champion_name)
        result = await search_for_champion(name)
        champion = alphabet(result)

        await ctx.send(f"{UGG}/{champion}/pro-build?region=kr")

    @commands.command()
    async def runes(self, ctx, *, champion_name: str):
        """
        *runes <name>

        A command that links you to a champion's most successful
        rune page in descending order.
        """

        name = alphabet(champion_name)
        result = await search_for_champion(name)
        champion = alphabet(result)

        await ctx.send(f"{UGG}/{champion}/rune-sets?rank=diamond_plus")

    @commands.command()
    async def spell(self, ctx, *, spell_name: str):
        """
        *spell <name>

        A command that displays a summoner spell's statistics.
        """

        async with ctx.typing():
            name = await search_for_spell(spell_name)
            spell = await get_spell_statistics(name)
            version = await get_spell_version(self.session)

            embed = discord.Embed(
                colour=self.viking.color
            )
            embed.set_thumbnail(
                url=f"{ASSET}/cdn/{version}/img/spell/{spell.full_image}"
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
                value=f"{spell.spell_range} units"
            )
            embed.add_field(
                inline=False,
                name='Cooldown',
                value=f"{spell.cooldown} seconds"
            )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.default)
    async def summoner(self, ctx, *, summoner_name: str):
        """
        *summoner <username>

        A command that provides you with information regarding a
        League of Legends account including: name, level, rank, points,
        win/loss ratio, and the top five champions with the highest
        mastery points.
        """

        try:
            get_summoner = await get_summoner_account(
                self.session,
                self.params,
                summoner_name
            )
        except RequestError:
            await ctx.send('No summoner found.')
        else:
            async with ctx.typing():
                summoner = Summoner(get_summoner)
                leagues = await get_summoner_leagues(
                    self.session,
                    self.params,
                    summoner.id
                )
                placement = await get_placement(leagues)
                champions = await get_mastery(
                    self.session,
                    self.params,
                    summoner.id
                )

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
