import discord
import time
from discord.ext import commands
from random import randint, choice


class Basic:
    def __init__(self, viking):
        self.viking = viking
        self.color = viking.color
        self.session = viking.session
        self.start_time = viking.start_time

    @commands.command()
    async def coinflip(self, ctx):
        """*coinflip

        A command that will flip a coin, and choose "Heads" or "Tails".
        """

        choices = (
            'Heads!',
            'Tails!'
        )

        await ctx.send(choice(choices))

    @commands.command()
    async def count(self, ctx, *, message):
        """*count <message>

        A command that will count the words in a message.
        """

        words = len(message.split())
        words = f"There are {words} words in this message."

        await ctx.send(words)

    @commands.command()
    async def dice(self, ctx):
        """*dice

        A command that will roll a dice, and select "1, 2, 3, 4, 5, 6".
        """

        choices = randint(1, 6)
        await ctx.send(choices)

    @commands.command()
    async def eightball(self, ctx, *, question):
        """*eightball <question>

        A command that will answer the author's question.
        """

        choices = (
            'Absolutely!',
            'Without a doubt.',
            'Most likely.',
            'Yes.',
            'Maybe.',
            'Perhaps.',
            'Nope.',
            'Very doubtful.',
            'Absolutely not.',
            'It is unlikely.'
        )

        await ctx.send(choice(choices))

    @commands.command()
    async def hello(self, ctx):
        """*hello

        A command that will respond with a random greeting.
        """

        choices = (
            'Hey!',
            'Hello!',
            'Hi!',
            'Hallo!',
            'Bonjour!',
            'Hola!'
        )

        await ctx.send(choice(choices))

    @commands.command()
    async def quotes(self, ctx):
        """*quotes

        A command that will return a random quotation.
        """

        params = {
            'method': 'getQuote',
            'lang': 'en',
            'format': 'json'
        }

        url = 'https://api.forismatic.com/api/1.0/'
        async with self.session.get(url, params=params) as response:
            data = await response.json(content_type=None)

            embed = discord.Embed(color=self.color)
            embed.add_field(name=data['quoteText'], value=f"- {data['quoteAuthor']}")
            await ctx.send(embed=embed)

    @commands.command()
    async def repeat(self, ctx, amount: int, *, message):
        """*repeat <amount> <message>

        A command that will repeat a message a specified amount of times.
        """

        if amount <= 5:
            for i in range(amount):
                await ctx.send(message)
        else:
            await ctx.send('Please use a number less than or equal to five.')

    @commands.command()
    async def reverse(self, ctx, *, message):
        """*reverse <message>

        A command that will reverse the words in an author's message.
        """

        message = message.split()
        await ctx.send(' '.join(reversed(message)))

    @commands.command()
    async def tts(self, ctx, *, message):
        """*tts <message>

        A command that will use to text-to-speech to repeat the author's
        message.
        """

        await ctx.send(message, tts=True)

    @commands.command()
    async def uptime(self, ctx):
        """*uptime

        A command that will return the bot's uptime.
        """

        uptime = round(time.time() - self.start_time)
        await ctx.send(uptime)


def setup(viking):
    viking.add_cog(Basic(viking))
