import discord
from discord.ext import commands
from utilities.exceptions import HTTPError


class Fortnite:
    def __init__(self, viking):
        self.viking = viking
        self.color = viking.color
        self.session = viking.session
        self.trn_api_key = viking.trn_api_key
        self.headers = {"trn-api-key": self.trn_api_key}

    def get(self, key, dict):
        """get(self, key, dict)

        A function that extracts the values from a dictionary
        for each key. If missing, the default is 0.
        """

        try:
            self.dictionary = dict.get(key, {})
            self.kills = self.dictionary.get('kills')['displayValue']
            self.matches = self.dictionary.get('matches')['displayValue']
            self.winratio = self.dictionary.get('winRatio')['displayValue']
            self.kd = self.dictionary.get('kd')['displayValue']
            self.wins = self.dictionary.get('top1')['displayValue']
        except TypeError:
            self.kills = 0
            self.matches = 0
            self.winratio = 0
            self.kd = 0.00
            self.wins = 0

        return self.kills, self.matches, self.winratio, self.kd, self.wins

    @commands.command(aliases=['fn'])
    @commands.cooldown(rate=1, per=3.0, type=commands.BucketType.default)
    async def fortnite(self, ctx, platform: str, *, username: str):
        """*fortnite <platform> <username>

        A command that will return a member's Fortnite statistics, including
        solo, duo, squad and total records.
        """

        url = f"https://api.fortnitetracker.com/v1/profile/{platform}/{username}"
        async with self.session.get(url, headers=self.headers) as response:
            if response.status != 200:
                raise HTTPError(url, response.status, response.reason)
                
            data = await response.json()

            try:
                gamemode = data['stats']
                lifetime = data['lifeTimeStats']
                embed = discord.Embed(title=username, colour=self.color)

                for key, gamemodes in [('p2', 'Solo:'), ('p10', 'Duo:'), ('p9', 'Squad:')]:
                    embed.add_field(
                        inline=False,
                        name=gamemodes,
                        value=f"""
                                Kills: {self.get(key, gamemode)[0]}
                                Matches: {self.get(key, gamemode)[1]}
                                Win Ratio: {self.get(key, gamemode)[2]}
                                K/D Ratio: {self.get(key, gamemode)[3]}
                                Wins: {self.get(key, gamemode)[4]}
                              """)

                embed.add_field(
                    inline=False,
                    name='Total:',
                    value=f"""
                            Kills: {lifetime[10]['value']}
                            Matches: {lifetime[7]['value']}
                            Win Ratio: {lifetime[9]['value']}
                            K/D Ratio: {lifetime[11]['value']}
                            Wins: {lifetime[8]['value']}
                          """)

                await ctx.send(embed=embed)
            except KeyError:
                await ctx.send(f"`{username}` does not exist.",
                               delete_after=10)


def setup(viking):
    viking.add_cog(Fortnite(viking))
