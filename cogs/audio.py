import asyncio
import discord
import os
import sys
from async_timeout import timeout
from discord.ext import commands
from rapidfuzz import process
from random import choice
from utilities.format import format_list


class Player:
    def __init__(self, ctx):
        self.viking = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.viking.loop.create_task(
            self.player_loop()
        )

    async def player_loop(self):
        await self.viking.wait_until_ready()

        while not self.viking.is_closed():
            self.next.clear()

            try:
                async with timeout(15):
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                    return self.destroy(self.guild)

            if self.guild.voice_client.is_connected():
                self.guild.voice_client.play(
                    source,
                    after=lambda _: self.viking.loop.call_soon_threadsafe(
                        self.next.set
                    )
                )

            await self.next.wait()

            source.cleanup()

    def destroy(self, guild):
        return self.viking.loop.create_task(
            self.cog.cleanup(guild)
        )


class Audio(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.players = {}
        self.root = viking.root

    @property
    def executable(self):
        if sys.platform == 'linux':
            return '/usr/bin/ffmpeg'
        else:
            return 'C:/Program Files/ffmpeg/bin/ffmpeg.exe'

    async def search_for_sound(self, query):
        sounds = os.listdir(f"{self.root}/soundbank")

        for sound in sounds:
            filename, extension = os.path.splitext(sound)

            if query == filename:
                return sound

        match = process.extractOne(query, sounds, score_cutoff=75)

        if match:
            return match[0]

        return None

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    def get_player(self, ctx):
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = Player(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command()
    async def connect(self, ctx, *, channel: discord.VoiceChannel = None):
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                pass

        if ctx.voice_client:
            if ctx.voice_client.channel.id == channel.id:
                return

            try:
                ctx.voice_client.pause()
                await ctx.voice_client.move_to(channel)
            except asyncio.TimeoutError:
                pass
            else:
                if ctx.voice_client.is_connected():
                    ctx.voice_client.resume()
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                pass

    @commands.command()
    async def play(self, ctx, *, query: str):
        """
        *play <sound>

        A command that plays a sound from the soundbank.
        """

        if query == 'random':
            sound = choice(
                os.listdir(f"{self.root}/soundbank")
            )
        else:
            sound = await self.search_for_sound(query)

            if sound is None:
                return

        source = discord.FFmpegPCMAudio(
            executable=self.executable,
            source=f"{self.root}/soundbank/{sound}"
        )

        if not ctx.voice_client:
            await ctx.invoke(self.connect)
        else:
            while True:
                await asyncio.sleep(1)

                if ctx.voice_client and not ctx.voice_client.is_playing():
                    break

            await ctx.invoke(self.connect)

        while not ctx.voice_client.is_connected():
            await asyncio.sleep(1)

            break

        player = self.get_player(ctx)
        await player.queue.put(source)

    @commands.command()
    async def pause(self, ctx):
        """
        *pause

        A command that pauses the current sound.
        """

        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return

        if ctx.voice_client.is_paused():
            return

        ctx.voice_client.pause()

    @commands.command()
    async def resume(self, ctx):
        """
        *resume

        A command that resumes the current sound.
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return

        if not ctx.voice_client.is_paused():
            return

        ctx.voice_client.resume()

    @commands.command()
    async def skip(self, ctx):
        """
        *skip

        A command that skips the current sound, and plays the next
        sound in the queue.
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return

        if ctx.voice_client.is_paused():
            pass

        if not ctx.voice_client.is_playing():
            return

        ctx.voice_client.stop()

    @commands.command()
    async def stop(self, ctx):
        """
        *stop

        A command that stops the current sound, and removes all
        sounds from the queue.
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return

        await self.cleanup(ctx.guild)

    @commands.command(aliases=['sound', 'sounds'])
    async def soundbank(self, ctx):
        """
        *soundbank

        A command that displays every sound in the soundbank.
        """

        directory = os.listdir(f"{self.root}/soundbank")
        soundbank = [os.path.splitext(files)[0] for files in directory]

        embed = discord.Embed(color=self.viking.color)
        embed.add_field(
            name='Soundbank',
            value=format_list(soundbank, sort=True)
        )

        await ctx.send(embed=embed)


def setup(viking):
    viking.add_cog(Audio(viking))
