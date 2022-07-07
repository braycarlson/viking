import asyncio
import discord
import time

from discord.ext import commands
from json import JSONDecodeError
from math import floor
from random import choice, randint, sample
from utilities.format import format_time, random_case
from utilities.request import fetch


class Basic(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
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

        selection = choice(choices)
        await ctx.send(selection)

    @commands.command()
    async def count(self, ctx, *, message):
        """
        *count <message>

        A command that counts the amount of words in a message.
        """

        message = message.split()
        length = len(message)

        await ctx.send(f"There are {length} word(s) in this message.")

    @commands.command()
    async def dice(self, ctx):
        """
        *dice

        A command that rolls a dice.
        """

        choices = randint(1, 6)
        await ctx.send(choices)

    @commands.command()
    @commands.has_any_role('Administrator', 'Moderator', 'OG')
    async def divide(self, ctx):
        """
        *divide

        A command that divides members into groups.
        """

        if ctx.author.voice:
            members = ctx.author.voice.channel.members
            length = len(members)

            if length > 1:
                amount = int(
                    floor(length / 2)
                )

                selected = sample(members, amount)

                channels = []

                for channel in ctx.guild.voice_channels:
                    if not channel.members:
                        channels.append(channel)

                selection = choice(channels)

                for member in selected:
                    await member.move_to(selection)

    @commands.command()
    async def eightball(self, ctx, *, question):
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

        selection = choice(choices)
        await ctx.send(selection)

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

        selection = choice(choices)
        await ctx.send(selection)

    @commands.command()
    async def mock(self, ctx, *, message):
        """
        *mock <message>

        A command that "mocks" a message.
        """

        await ctx.message.delete()

        message = random_case(message)
        await ctx.send(message)

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
            response = await fetch(
                self.viking.session,
                url,
                params=params
            )
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
    async def repeat(self, ctx, amount, *, message):
        """
        *repeat <amount> <message>

        A command that repeats the message a specified amount of times.
        """

        amount = int(amount)

        if amount <= 5:
            for i in range(amount):
                await ctx.send(message)
        else:
            await ctx.send('Please use a number less than or equal to five.')

    @commands.command()
    async def reverse(self, ctx, *, message):
        """
        *reverse <message>

        A command that reverses the words in a message.
        """

        message = message.split()

        reverse = ' '.join(
            reversed(message)
        )

        await ctx.send(reverse)

    @commands.command()
    async def tts(self, ctx, *, message):
        """
        *tts <message>

        A command that uses to text-to-speech to repeat a message.
        """

        await ctx.message.delete()
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
        months, weeks = divmod(weeks, 4)
        years, months = divmod(months, 52)

        year = format_time(years, 'year', delimiter=True)
        month = format_time(months, 'month', delimiter=True)
        week = format_time(weeks, 'week', delimiter=True)
        day = format_time(days, 'day', delimiter=True)
        hour = format_time(hours, 'hour', delimiter=True)
        minute = format_time(minutes, 'minute', delimiter=True)
        second = format_time(seconds, 'second')

        await ctx.send(f"{year} {month} {week} {day} {hour} {minute} {second}")


async def setup(viking):
    basic = Basic(viking)
    await viking.add_cog(basic)
