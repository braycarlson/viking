import asyncio
import discord
import time
from discord.ext import commands
from json import JSONDecodeError
from random import randint, choice
from utilities.format import format_time
from utilities.request import fetch


class Basic(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.session = viking.session
        self.start_time = viking.start_time

    @commands.command()
    async def coinflip(self, ctx):
        """
        *coinflip

        A command that flips a coin.
        """

        choices = (
            'Heads!',
            'Tails!'
        )

        await ctx.send(choice(choices))

    @commands.command()
    async def count(self, ctx, *, message: str):
        """
        *count <message>

        A command that counts the amount of words in a message.
        """

        words = len(message.split())
        await ctx.send(f"There are {words} words in this message.")

    @commands.command()
    async def dice(self, ctx):
        """
        *dice

        A command that rolls a dice.
        """

        choices = randint(1, 6)
        await ctx.send(choices)

    @commands.command()
    async def eightball(self, ctx, *, question: str):
        """
        *eightball <question>

        A command that answers a closed question.
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
        """
        *hello

        A command that displays a random greeting.
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
        """
        *quotes

        A command that displays a random quotation.
        """

        params = {
            'method': 'getQuote',
            'lang': 'en',
            'format': 'json'
        }

        url = 'https://api.forismatic.com/api/1.0/'

        # The Forismatic API will occassionally return malformed JSON,
        # so reinvoke the command, until we recieve a proper response.

        try:
            response = await fetch(self.session, url, params=params)
        except JSONDecodeError:
            await asyncio.sleep(1)
            await ctx.reinvoke()
        else:
            quote = response.get('quoteText')
            author = response.get('quoteAuthor')

            if not author:
                author = 'Unknown'

            embed = discord.Embed(color=self.viking.color)
            embed.add_field(name=quote, value=f"- {author}")
            await ctx.send(embed=embed)

    @commands.command()
    async def repeat(self, ctx, amount: int, *, message: str):
        """
        *repeat <amount> <message>

        A command that repeats the message a specified amount of times.
        """

        if amount <= 5:
            for i in range(amount):
                await ctx.send(message)
        else:
            await ctx.send('Please use a number less than or equal to five.')

    @commands.command()
    async def reverse(self, ctx, *, message: str):
        """
        *reverse <message>

        A command that reverses the words in a message.
        """

        message = message.split()
        await ctx.send(' '.join(reversed(message)))

    @commands.command()
    async def tts(self, ctx, *, message: str):
        """
        *tts <message>

        A command that uses to text-to-speech to repeat a message.
        """

        await ctx.send(message, tts=True)

    @commands.command()
    async def uptime(self, ctx):
        """
        *uptime

        A command that displays the bot's uptime.
        """

        duration = round(time.time() - self.start_time)
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        weeks, days = divmod(days, 7)

        w = format_time(weeks, 'week', delimiter=True)
        d = format_time(days, 'day', delimiter=True)
        h = format_time(hours, 'hour', delimiter=True)
        m = format_time(minutes, 'minute', delimiter=True)
        s = format_time(seconds, 'second')

        await ctx.send(f"{w} {d} {h} {m} {s}")


def setup(viking):
    viking.add_cog(Basic(viking))
