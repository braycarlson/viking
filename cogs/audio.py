from __future__ import annotations

import asyncio
import contextlib
import discord
import logging
import os
import sys

from async_timeout import timeout
from datetime import datetime, timezone
from discord.ext import commands
from pages.audio import MySoundsPages, SoundPages
from pathlib import Path
from rapidfuzz import process
from sqlalchemy.dialects.postgresql import insert
from typing import TYPE_CHECKING
from utilities.format import alphanumerical
from utilities.member import MemberInterface
from utilities.request import download

if TYPE_CHECKING:
    from bot import Viking
    from discord import Guild, Message
    from discord.ext.commands import Context


log = logging.getLogger(__name__)


class Player:
    def __init__(self, ctx: Context):
        self.viking = ctx.bot
        self.cog = ctx.cog
        self.guild = ctx.guild

        self.queue = asyncio.Queue()
        self.event = asyncio.Event()

        self.viking.loop.create_task(
            self.player_loop()
        )

    async def player_loop(self) -> None:
        await self.viking.wait_until_ready()

        source = None

        while not self.viking.is_closed():
            self.event.clear()

            try:
                async with timeout(30):
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self.guild)

            self.guild.voice_client.play(
                source,
                after=lambda _: self.viking.loop.call_soon_threadsafe(
                    self.event.set
                )
            )

            await self.event.wait()

        if source is not None:
            source.cleanup()

        return source

    def destroy(self, guild: Guild) -> None:
        return self.viking.loop.create_task(
            self.cog.cleanup(guild)
        )


class Audio(commands.Cog):
    def __init__(self, viking: Viking):
        self.viking = viking
        self.player = {}
        self.root = viking.root
        self.default = self.root.joinpath('sound/default')
        self.member = self.root.joinpath('sound/member')

    @property
    def executable(self) -> Path:
        if sys.platform == 'linux':
            return Path('/usr/bin/ffmpeg')

        return Path('C:/Program Files/ffmpeg/bin/ffmpeg.exe')

    def get_player(self, ctx: Context) -> Player:
        try:
            player = self.player[ctx.guild.id]
        except KeyError:
            player = Player(ctx)
            self.player[ctx.guild.id] = player

        return player

    def get_soundbank(self) -> list[Path]:
        return self.ls(self.default) + self.ls(self.member)

    def ls(self, directory: Path | str) -> list[Path]:
        return [
            path
            for path in directory.iterdir()
        ]

    async def get_file(self, query: str) -> Path | None:
        soundbank = self.get_soundbank()

        for sound in soundbank:
            if query == sound.stem:
                return sound

        return None

    async def search_for_sound(self, query: str) -> Path | None:
        soundbank = self.get_soundbank()

        for sound in soundbank:
            if query == sound.stem:
                return sound

        sound = {sound.stem: sound for sound in soundbank}

        match = process.extractOne(
            query,
            sound.keys(),
            score_cutoff=75
        )

        if match:
            filename, *_ = match
            return sound.get(filename)

        return None

    async def cleanup(self, guild: Guild) -> None:
        with contextlib.suppress(AttributeError):
            await guild.voice_client.disconnect()

        with contextlib.suppress(KeyError):
            del self.player[guild.id]

    @commands.command()
    async def add(self, ctx: Context, *, name: str = None) -> Message:
        """
        *add <filename>

        A command that adds a sound from a member.
        """

        filetype = [
            '.aac',
            '.aiff',
            '.flac',
            '.m4a',
            '.mp3',
            '.ogg',
            '.wav',
            '.wmv'
        ]

        for attachment in ctx.message.attachments:
            path = Path(attachment.filename)
            extension = path.suffix.lower()

            if extension in filetype:
                if name is None:
                    name = alphanumerical(path.stem).lower()
                else:
                    name = alphanumerical(name).lower()

                filename = f'{name}{extension}'
                default = self.default.joinpath(filename)
                member = self.member.joinpath(filename)

                if 'random' in member.stem or 'random' in default.stem:
                    return await ctx.send('Please use another filename.')

                if member.exists() or default.exists():
                    return await ctx.send(f"'{name}' already exists. Please use another filename.")

                await download(self.viking.session, attachment.url, member)

                date = datetime.now(timezone.utc)

                await self.viking.guild.sound.create(
                    name=name,
                    created_by=ctx.author.id,
                    created_at=date
                )

                await ctx.send(f'Command was successfully added. Please use: ***play {name}**')

            return await ctx.send(f"{extension} is not a supported filetype.")

        return None

    @commands.command()
    async def connect(self, ctx: Context, *, channel = None) -> None:
        if not channel:
            with contextlib.suppress(AttributeError):
                channel = ctx.author.voice.channel

        if ctx.voice_client:
            if ctx.voice_client.channel.id == channel.id:
                return

            while True:
                await asyncio.sleep(1)

                if not ctx.voice_client.is_playing():
                    break

            await ctx.voice_client.disconnect()

        with contextlib.suppress(asyncio.TimeoutError):
            await channel.connect()

    @commands.command()
    async def delete(self, ctx: Context, query: str) -> Message:
        """
        *delete <sound>

        A command that deletes the sound uploaded by the author.
        """

        row = (
            await self.viking.guild.sound
            .select('id', 'created_by')
            .where(self.viking.guild.sound.created_by == ctx.author.id)
            .where(self.viking.guild.sound.name == query)
            .gino
            .first()
        )

        if row is None:
            message = f"You do not have permission to delete **{query}**."
            return await ctx.send(message)

        file = await self.get_file(query)
        self.member.joinpath(file.stem + file.suffix).unlink()

        (
            await self.viking.guild.sound
            .delete
            .where(self.viking.guild.sound.name == query)
            .gino
            .status()
        )

        message = f"**{query}** was successfully deleted."
        return await ctx.send(message)

    @commands.command()
    async def mysounds(self, ctx: Context) -> None:
        """
        *mysounds

        A command that displays all sounds uploaded by the author.
        """

        rows = (
            await self.viking.guild.sound
            .select('name')
            .where(self.viking.guild.sound.created_by == ctx.author.id)
            .gino
            .all()
        )

        sounds = sorted(
            [
                dict(row).get('name')
                for row in rows
            ]
        )

        sound = [
            sounds[i:i + 75]
            for i in range(0, len(sounds), 75)
        ]

        try:
            pages = MySoundsPages(ctx, ctx.author.display_name, sound)
            await pages.paginate()
        except Exception as exception:
            log.info(exception)

    @commands.command()
    async def play(self, ctx: Context, *, query: str) -> Message | None:
        """
        *play <sound>

        A command that plays a sound from the soundbank.
        """

        if query == 'random':
            soundbank = self.get_soundbank()
            sound = self.viking.random.choice(soundbank)
        else:
            sound = await self.search_for_sound(query)

        if sound is None:
            return await ctx.send(f"'{query}' could not be found.")

        source = discord.FFmpegPCMAudio(
            executable=self.executable,
            source=sound
        )

        await ctx.invoke(self.connect)

        while not ctx.voice_client.is_connected():
            await asyncio.sleep(1)

            break

        player = self.get_player(ctx)
        await player.queue.put(source)

        return None

    @commands.command()
    async def pause(self, ctx: Context) -> None:
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
    async def rename(self, ctx: Context, before: str, after: str) -> Message:
        """
        *rename <before> <after>

        A command to rename a sound.
        """

        row = (
            await self.viking.guild.sound
            .select('id', 'created_by')
            .where(self.viking.guild.sound.created_by == ctx.author.id)
            .where(self.viking.guild.sound.name == before)
            .gino
            .first()
        )

        if row is None:
            message = f"You do not have permission to modify **{before}**."
            return await ctx.send(message)

        file = await self.get_file(before)
        before = self.member.joinpath(file.stem + file.suffix)
        after = self.member.joinpath(alphanumerical(after) + file.suffix)
        os.rename(before, after)

        id, created_by = row
        updated_at = datetime.now(timezone.utc)

        statement = (
            insert(self.viking.guild.sound)
            .values(
                id=id,
                name=after,
                created_by=created_by,
                updated_at=updated_at
            )
        )

        statement = (
            await statement
            .on_conflict_do_update(
                index_elements=[self.viking.guild.sound.id],
                set_={
                    'id': statement.excluded.id,
                    'name': statement.excluded.name,
                    'created_by': statement.excluded.created_by,
                    'updated_at': statement.excluded.updated_at
                }
            )
            .gino
            .scalar()
        )

        message = f"{before} was successfully renamed to **{after}**."
        return await ctx.send(message)

    @commands.command()
    async def resume(self, ctx: Context) -> None:
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
    async def skip(self, ctx: Context) -> None:
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
    async def stop(self, ctx: Context) -> None:
        """
        *stop

        A command that stops the current sound, and removes all
        sounds from the queue.
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return

        await self.cleanup(ctx.guild)

    @commands.command()
    async def soundsfrom(self, ctx: Context, *, identifier: str) -> Message | None:
        """
        *soundsfrom <identifier>

        A command that displays all sounds uploaded by a
        specified member.
        """

        interface = MemberInterface(ctx, identifier)
        discord_id = await interface.get()

        if discord_id is None:
            return None

        row = dict(
            await self.viking.guild.member
            .select('discord_id', 'display_name')
            .where(self.viking.guild.member.discord_id == discord_id)
            .gino
            .first()
        )

        discord_id = row.get('discord_id')
        display_name = row.get('display_name')

        rows = (
            await self.viking.guild.sound
            .select('name')
            .where(self.viking.guild.sound.created_by == discord_id)
            .gino
            .all()
        )

        if not rows:
            return await ctx.send(f"{display_name} hasn't uploaded a sound.")

        sounds = sorted([dict(row).get('name') for row in rows])
        sound = [sounds[i:i + 75] for i in range(0, len(sounds), 75)]

        try:
            pages = MySoundsPages(ctx, display_name, sound)
            await pages.paginate()
        except Exception as exception:
            log.info(exception)

    @commands.command(aliases=['sound', 'sounds'])
    async def soundbank(self, ctx: Context) -> None:
        """
        *soundbank

        A command that displays every sound in the soundbank.
        """

        soundbank = self.get_soundbank()
        sounds = sorted([sound.stem for sound in soundbank])
        sound = [sounds[i:i + 75] for i in range(0, len(sounds), 75)]

        try:
            pages = SoundPages(ctx, sound)
            await pages.paginate()
        except Exception as exception:
            log.info(exception)
        finally:
            await ctx.message.delete()


async def setup(viking: Viking) -> None:
    audio = Audio(viking)
    await viking.add_cog(audio)
