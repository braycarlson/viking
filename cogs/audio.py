import asyncio
import discord
import os
import sys
from async_timeout import timeout
from database.model import ActiveMembers, MemberSounds
from datetime import datetime
from discord.ext import commands
from pathlib import Path, PurePath
from random import choice
from rapidfuzz import process
from sqlalchemy.dialects.postgresql import insert
from utilities.format import alphanumerical, format_list
from utilities.member import MemberError, get_member_by_id
from utilities.pagination import Pages
from utilities.request import download


class MySoundsPages(Pages):
    def __init__(self, ctx, member, entries):
        super().__init__(ctx, entries=entries, per_page=1)
        self.member = member

    def get_page(self, page):
        return self.entries[page - 1]

    def prepare_embed(self, entries, page, *, first=False):
        self.embed = embed = discord.Embed(
            colour=discord.Colour.purple(),
            title=f"{self.member}'s Sounds"
        )

        embed.add_field(
            inline=False,
            name='Sound',
            value=format_list(entries, paragraph=True)
        )

        if self.maximum_pages > 1:
            text = f'Page {page}/{self.maximum_pages}'
            embed.set_footer(text=text)


class SoundPages(Pages):
    def __init__(self, ctx, entries):
        super().__init__(ctx, entries=entries, per_page=1)

    def get_page(self, page):
        return self.entries[page - 1]

    def prepare_embed(self, entries, page, *, first=False):
        self.embed = embed = discord.Embed(
            colour=discord.Colour.purple(),
            title='Soundbank'
        )

        embed.add_field(
            inline=False,
            name='Sound',
            value=format_list(entries, paragraph=True)
        )

        if self.maximum_pages > 1:
            text = f'Page {page}/{self.maximum_pages}'
            embed.set_footer(text=text)


class Player:
    def __init__(self, ctx):
        self.viking = ctx.bot
        self.guild = ctx.guild
        self.cog = ctx.cog

        self.queue = asyncio.Queue()
        self.event = asyncio.Event()

        self.viking.loop.create_task(
            self.player_loop()
        )

    async def player_loop(self):
        await self.viking.wait_until_ready()

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
            source.cleanup()

    def destroy(self, guild):
        return self.viking.loop.create_task(
            self.cog.cleanup(guild)
        )


class Audio(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.player = {}
        self.root = viking.root
        self.default = self.root.joinpath('sound/default')
        self.member = self.root.joinpath('sound/member')
        self.session = viking.session

    @property
    def executable(self):
        if sys.platform == 'linux':
            return PurePath('/usr/bin/ffmpeg')
        else:
            return PurePath('C:/Program Files/ffmpeg/bin/ffmpeg.exe')

    def get_player(self, ctx):
        try:
            player = self.player[ctx.guild.id]
        except KeyError:
            player = Player(ctx)
            self.player[ctx.guild.id] = player

        return player

    def get_soundbank(self):
        return self.ls(self.default) + self.ls(self.member)

    def ls(self, directory):
        file = [path for path in directory.iterdir()]
        return file

    async def get_file(self, query):
        soundbank = self.get_soundbank()

        for sound in soundbank:
            if query == sound.stem:
                return sound

    async def search_for_sound(self, query):
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
            filename, _ = match
            path = sound.get(filename)
            return path

        return None

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.player[guild.id]
        except KeyError:
            pass

    @commands.command()
    @commands.has_any_role('Administrator', 'Moderator', 'OG')
    async def add(self, ctx, *, name=None):
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
                else:
                    await download(self.session, attachment.url, member)

                    date = datetime.now()

                    await MemberSounds.create(
                        name=name,
                        created_by=ctx.author.id,
                        created_at=date
                    )

                    await ctx.send(f'Command was successfully added. Please use: ***play {name}**')
            else:
                return await ctx.send(f"{extension} is not a supported filetype.")

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

            while True:
                await asyncio.sleep(1)

                if not ctx.voice_client.is_playing():
                    break

            await ctx.voice_client.disconnect()

        try:
            await channel.connect()
        except asyncio.TimeoutError:
            pass

    @commands.command()
    async def delete(self, ctx, query: str):
        """
        *delete <sound>

        A command that deletes the sound uploaded by the author.
        """

        row = (
            await MemberSounds
            .select('id', 'created_by')
            .where(MemberSounds.created_by == ctx.author.id)
            .where(MemberSounds.name == query)
            .gino
            .first()
        )

        if row is None:
            message = f"You do not have permission to delete **{query}**."
            return await ctx.send(message)

        file = await self.get_file(query)
        self.member.joinpath(file.stem + file.suffix).unlink()

        (
            await MemberSounds
            .delete
            .where(MemberSounds.name == query)
            .gino
            .status()
        )

        message = f"**{query}** was successfully deleted."
        await ctx.send(message)

    @commands.command()
    async def mysounds(self, ctx):
        """
        *mysounds

        A command that displays all sounds uploaded by the author.
        """

        rows = (
            await MemberSounds
            .select('name')
            .where(MemberSounds.created_by == ctx.author.id)
            .gino
            .all()
        )

        sounds = sorted([dict(row).get('name') for row in rows])
        sound = [sounds[i:i + 75] for i in range(0, len(sounds), 75)]

        try:
            pages = MySoundsPages(ctx, ctx.author.display_name, sound)
            await pages.paginate()
        except Exception:
            pass

    @commands.command()
    async def play(self, ctx, *, query: str):
        """
        *play <sound>

        A command that plays a sound from the soundbank.
        """

        if query == 'random':
            soundbank = self.get_soundbank()
            sound = choice(soundbank)
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
    async def rename(self, ctx, before: str, after: str):
        """
        *rename <before> <after>

        A command to rename a sound.
        """

        row = (
            await MemberSounds
            .select('id', 'created_by')
            .where(MemberSounds.created_by == ctx.author.id)
            .where(MemberSounds.name == before)
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
        updated_at = datetime.now()

        statement = (
            insert(MemberSounds)
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
                index_elements=[MemberSounds.id],
                set_=dict(
                    id=statement.excluded.id,
                    name=statement.excluded.name,
                    created_by=statement.excluded.created_by,
                    updated_at=statement.excluded.updated_at
                )
            )
            .gino
            .scalar()
        )

        message = f"{before} was successfully renamed to **{after}**."
        await ctx.send(message)

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

    @commands.command()
    async def soundsfrom(self, ctx, *, identifier):
        """
        *soundsfrom <identifier>

        A command that displays all sounds uploaded by a
        specified member.
        """

        try:
            member_id = await get_member_by_id(self, ctx, identifier)
        except MemberError:
            await ctx.send('No member found.')
        except TimeoutError:
            await ctx.send('You have run out of time. Please try again.')

        row = dict(
            await ActiveMembers
            .select('discord_id', 'display_name')
            .where(ActiveMembers.discord_id == member_id)
            .gino
            .first()
        )

        discord_id = row.get('discord_id')
        display_name = row.get('display_name')

        rows = (
            await MemberSounds
            .select('name')
            .where(MemberSounds.created_by == discord_id)
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
        except Exception:
            pass

    @commands.command(aliases=['sound', 'sounds'])
    async def soundbank(self, ctx):
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
        except Exception:
            pass
        finally:
            await ctx.message.delete()


def setup(viking):
    viking.add_cog(Audio(viking))
