from __future__ import annotations

import time

from typing_extensions import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from basic import embeds
from core.http import RequestError, fetch
from core.text import random_case
from core.time import (
    SECONDS_PER_DAY,
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
    time_format,
)

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from bot import Viking


DICE_SIDES = 6
QUOTE_URL = 'https://zenquotes.io/api/random'


class Basic(commands.Cog):
    def __init__(self, viking: Viking) -> None:
        self.viking = viking

    @commands.hybrid_command(description='Flip a coin.')
    async def coinflip(self, ctx: Context) -> None:
        """
        *coinflip

        A command that flips a coin.
        """

        choices = ('Heads!', 'Tails!')

        selection = self.viking.random.choice(choices)
        await ctx.send(selection)

    @commands.hybrid_command(description='Count the number of words in a message.')
    @app_commands.describe(message='The message to count the words of.')
    async def count(self, ctx: Context, *, message: str) -> None:
        """
        *count <message>

        A command that counts the amount of words in a message.
        """

        words = message.split()
        length = len(words)

        reply = f'There are {length} word(s) in this message.'
        await ctx.send(reply)

    @commands.hybrid_command(description='Roll a dice.')
    async def dice(self, ctx: Context) -> None:
        """
        *dice

        A command that rolls a dice.
        """

        result = self.viking.random.randint(1, DICE_SIDES)

        message = str(result)
        await ctx.send(message)

    @commands.hybrid_command(description='Divide the voice channel members into groups.')
    @commands.bot_has_guild_permissions(move_members=True)
    @commands.has_guild_permissions(move_members=True)
    async def divide(self, ctx: Context) -> None:
        """
        *divide

        A command that divides members into groups.
        """

        await ctx.typing()

        voice = ctx.author.voice

        if voice is None or voice.channel is None:
            message = 'You must be in a voice channel.'
            await ctx.send(message)

            return

        members = voice.channel.members
        length = len(members)

        if length < 2:
            message = 'There must be another member present.'
            await ctx.send(message)

            return

        amount = length // 2
        selected = self.viking.random.sample(members, amount)

        afk = ctx.guild.afk_channel

        available_channels = [
            channel
            for channel in ctx.guild.voice_channels
            if channel != afk and channel.user_limit == 0 and not channel.members
        ]

        if not available_channels:
            message = 'No available voice channels found.'
            await ctx.send(message)

            return

        selection = self.viking.random.choice(available_channels)

        for member in selected:
            await member.move_to(selection)

    @commands.hybrid_command(description='Answer a closed question.')
    @app_commands.describe(question='The question to answer.')
    async def eightball(self, ctx: Context, *, question: str) -> None:  # noqa: ARG002
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

        selection = self.viking.random.choice(choices)
        await ctx.send(selection)

    @commands.hybrid_command(description='Display a random greeting.')
    async def hello(self, ctx: Context) -> None:
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

        selection = self.viking.random.choice(choices)
        await ctx.send(selection)

    @commands.hybrid_command(description='Mock a message.')
    @app_commands.describe(message='The message to mock.')
    async def mock(self, ctx: Context, *, message: str) -> None:
        """
        *mock <message>

        A command that "mocks" a message.
        """

        if ctx.message is not None:
            await ctx.message.delete()

        mocked = random_case(message)
        await ctx.send(mocked)

    @commands.hybrid_command(description='Display a random quotation.')
    async def quotes(self, ctx: Context) -> None:
        """
        *quotes

        A command that displays a random quotation.
        """

        await ctx.typing()

        try:
            response = await fetch(self.viking.session, QUOTE_URL)
        except RequestError:
            message = 'Failed to fetch a quote. Please try again.'
            await ctx.send(message)

            return

        entry = response[0]
        quote = entry.get('q')
        author = entry.get('a') or 'Unknown'

        embed = embeds.quote_embed(quote, author, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Repeat a message a number of times.')
    @app_commands.describe(
        amount='How many times to repeat the message (1-5).',
        message='The message to repeat.'
    )
    async def repeat(
        self,
        ctx: Context,
        amount: commands.Range[int, 1, 5],
        *,
        message: str
    ) -> None:
        """
        *repeat <amount> <message>

        A command that repeats the message a specified amount of times.
        """

        for _ in range(amount):
            await ctx.send(message)

    @commands.hybrid_command(description='Reverse the words in a message.')
    @app_commands.describe(message='The message to reverse.')
    async def reverse(self, ctx: Context, *, message: str) -> None:
        """
        *reverse <message>

        A command that reverses the words in a message.
        """

        words = message.split()
        reverse = ' '.join(reversed(words))

        await ctx.send(reverse)

    @commands.hybrid_command(description='Repeat a message using text-to-speech.')
    @app_commands.describe(message='The message to repeat.')
    async def tts(self, ctx: Context, *, message: str) -> None:
        """
        *tts <message>

        A command that uses to text-to-speech to repeat a message.
        """

        if ctx.message is not None:
            await ctx.message.delete()

        await ctx.send(message, tts=True)

    @commands.hybrid_command(description="Display the bot's uptime.")
    async def uptime(self, ctx: Context) -> None:
        """
        *uptime

        A command that displays the bot's uptime.
        """

        duration = round(time.time() - self.viking.start_time)

        days, remainder = divmod(duration, SECONDS_PER_DAY)
        hours, remainder = divmod(remainder, SECONDS_PER_HOUR)
        minutes, seconds = divmod(remainder, SECONDS_PER_MINUTE)

        parts = []

        if days:
            part = time_format(days, 'day', delimiter=True)
            parts.append(part)

        if hours:
            part = time_format(hours, 'hour', delimiter=True)
            parts.append(part)

        if minutes:
            part = time_format(minutes, 'minute', delimiter=True)
            parts.append(part)

        part = time_format(seconds, 'second')
        parts.append(part)

        message = ' '.join(parts)
        await ctx.send(message)


async def setup(viking: Viking) -> None:
    basic = Basic(viking)
    await viking.add_cog(basic)
