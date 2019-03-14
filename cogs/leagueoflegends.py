import discord
import logging
from discord.ext import commands
from utilities.exceptions import HTTPError


log = logging.getLogger(__name__)


class LeagueOfLegends:
    def __init__(self, viking):
        self.viking = viking
        self.color = viking.color
        self.lol_api_key = viking.lol_api_key
        self.params = {'api_key': self.lol_api_key}
        self.session = viking.session

    async def get_current_version(self):
        url = 'https://ddragon.leagueoflegends.com/realms/na.json'
        async with self.session.get(url, params=self.params) as response:
            if response.status != 200:
                raise HTTPError(url, response.status, response.reason)

            return await response.json()

    async def get_all_champions(self):
        version = await self.get_current_version()

        url = f"http://ddragon.leagueoflegends.com/cdn/{version['v']}/data/en_US/champion.json"
        async with self.session.get(url, params=self.params) as response:
            if response.status != 200:
                raise HTTPError(url, response.status, response.reason)

            return await response.json()

    async def get_champion_name(self, champion_id):
        champions = await self.get_all_champions()

        for champion in champions['data'].values():
            if str(champion_id) == champion['key']:
                return champion['name']

    async def get_champion_mastery(self, summoner_id):
        url = f"https://na1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/{summoner_id}"
        async with self.session.get(url, params=self.params) as response:
            if response.status != 200:
                raise HTTPError(url, response.status, response.reason)

            return await response.json()

    async def get_summoner_account(self, summoner):
        url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner}"
        async with self.session.get(url, params=self.params) as response:
            if response.status != 200:
                raise HTTPError(url, response.status, response.reason)

            return await response.json()

    async def get_summoner_leagues(self, summoner_id):
        url = f"https://na1.api.riotgames.com/lol/league/v4/positions/by-summoner/{summoner_id}"
        async with self.session.get(url, params=self.params) as response:
            if response.status != 200:
                raise HTTPError(url, response.status, response.reason)

            return await response.json()

    async def get_active_game(self, summoner):
        player = await self.get_summoner_account(summoner)

        url = f"https://na1.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{player['id']}"
        async with self.session.get(url, params=self.params) as response:
            if response.status != 200:
                raise HTTPError(url, response.status, response.reason)

            return await response.json()

    @commands.command()
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.default)
    async def live(self, ctx, *, summoner):
        """*live <username>

        A command that will give an overview of everyone in your current game
        including: everyone's name, level, champion, rank and win/loss ratio"""

        game = await self.get_active_game(summoner)
        blue = discord.Embed(title='Blue Team:', colour=discord.Colour.blue())
        red = discord.Embed(title='Red Team:', colour=discord.Colour.red())

        for player in game['participants']:
            ranked = []
            name = player['summonerName']
            summoner = await self.get_summoner_leagues(player['summonerId'])
            champion = await self.get_champion_name(player['championId'])

            for info in summoner:
                if 'RANKED_SOLO_5x5' in info['queueType']:
                    ranked.append(info['summonerName'])
                    tier = info['tier'].title()
                    rank = info['rank']
                    wins = info['wins']
                    losses = info['losses']
                    games = wins + losses
                    win_loss = f"[{wins / games * 100:0.2f}%]"
                    lp = f"[{info['leaguePoints']} LP]"

            if player['teamId'] == 100:
                if ranked:
                    blue.add_field(
                            inline=False,
                            name=f"**{name}**",
                            value=f"{champion} - {tier} {rank} {lp} {win_loss}")
                else:
                    blue.add_field(
                            inline=False,
                            name=f"**{name}**",
                            value=f"{champion} - Unranked")
            else:
                if ranked:
                    red.add_field(
                            inline=False,
                            name=f"**{name}**",
                            value=f"{champion} - {tier} {rank} {lp} {win_loss}")
                else:
                    red.add_field(
                            inline=False,
                            name=f"**{name}**",
                            value=f"{champion} - Unranked")

        await ctx.send(embed=blue)
        await ctx.send(embed=red)

    @commands.command()
    async def summoner(self, ctx, *, summoner):
        """*summoner <username>

        A command that will provide you with information regarding your League
        of Legends account including: name, level, rank, points, win/loss ratio,
        and your top five champions with the highest mastery points."""

        champions = []
        player = await self.get_summoner_account(summoner)
        mastery = await self.get_champion_mastery(player['id'])
        leagues = await self.get_summoner_leagues(player['id'])
        embed = discord.Embed(
            title=f"{player['name']} (Level {player['summonerLevel']})",
            colour=self.color)

        if leagues:
            for info in leagues:
                if 'RANKED_SOLO_5x5' in info['queueType']:
                    queue = '**Solo Queue**:'
                elif 'RANKED_FLEX_SR' in info['queueType']:
                    queue = '**Flex Queue (5x5)**:'
                else:
                    queue = '**Flex Queue (3x3)**:'

                tier = info['tier'].title()
                rank = info['rank']
                wins = info['wins']
                losses = info['losses']
                games = wins + losses
                win_loss = f"[{wins / games * 100:0.2f}%]"
                lp = f"[{info['leaguePoints']} LP]"

                embed.add_field(
                    inline=False,
                    name=queue,
                    value=f"{tier} {rank} {lp} {win_loss}")
        else:
            embed.add_field(
                inline=False,
                name='**Solo and Flex Queue**:',
                value=f"Unranked")

        for champion in mastery[:5]:
            name = await self.get_champion_name(champion['championId'])
            champions.append(name)

        embed.add_field(
            inline=False,
            name='**Top Champions**:',
            value=f"{', '.join(champions)}")

        await ctx.send(embed=embed)


def setup(viking):
    viking.add_cog(LeagueOfLegends(viking))
