from __future__ import annotations

import asyncio
import contextlib
import sys

import discord

from functools import partial
from pathlib import Path
from typing_extensions import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands
from rapidfuzz import process

from audio.autocomplete import sound_autocomplete
from audio.modals import SoundUploadModal
from audio.player import Player
from audio.repository import SoundRepository
from audio.views import AudioControlView, audio_browser_create, theme_browser_create
from core.http import download
from core.text import alphanumerical
from members.autocomplete import member_autocomplete
from members.interface import identifier_get
from members.repository import MemberRepository

if TYPE_CHECKING:
    from discord import Guild
    from discord.ext.commands import Context

    from bot import Viking


SUPPORTED_FILETYPES = frozenset({
    '.aac',
    '.aiff',
    '.flac',
    '.m4a',
    '.mp3',
    '.ogg',
    '.wav',
    '.wmv'
})

BYTES_PER_MEGABYTE = 1024 * 1024

ATTACHMENT_BYTES_MAX = 8 * BYTES_PER_MEGABYTE
RANDOM_SOUND = 'random'
SOUND_MATCH_SCORE_MIN = 75
VOICE_CONNECT_DELAY_SECONDS = 1


class Audio(commands.Cog):
    def __init__(self, viking: Viking) -> None:
        self.viking = viking

        self.default_directory = viking.sound.joinpath('default')
        self.member_directory = viking.sound.joinpath('member')
        self.players: dict[int, Player] = {}
        self.views: dict[int, AudioControlView] = {}

    @property
    def executable(self) -> str:
        if sys.platform == 'linux':
            return '/usr/bin/ffmpeg'

        return 'ffmpeg'

    @property
    def sounds(self) -> SoundRepository:
        return SoundRepository(self.viking.guild.session)

    async def _on_track_end(self, guild_identifier: int) -> None:
        view = self.views.get(guild_identifier)

        if view is None or view.message is None:
            return

        view.now_playing_clear()

        with contextlib.suppress(discord.HTTPException):
            await view.message.edit(view=view)

    def _sound_map_build(self) -> dict[str, Path]:
        return {sound.stem: sound for sound in self.soundbank_get()}

    async def _sound_play(self, ctx: Context, sound: Path) -> None:
        source = discord.FFmpegPCMAudio(
            executable=self.executable,
            source=str(sound)
        )

        await ctx.invoke(self.connect)

        if ctx.voice_client and not ctx.voice_client.is_connected():
            await asyncio.sleep(VOICE_CONNECT_DELAY_SECONDS)

        player = self.player_get(ctx)
        callback = partial(self._on_track_end, ctx.guild.id)

        await player.queue.put((source, callback))

    async def _sound_play_by_name(self, ctx: Context, name: str) -> bool:
        sound = self.sound_search(name)

        if sound is None:
            return False

        await self._sound_play(ctx, sound)
        return True

    async def _sound_store(
        self,
        attachment: discord.Attachment,
        name: str | None,
        author_identifier: int
    ) -> str:
        path = Path(attachment.filename)
        extension = path.suffix.lower()

        if extension not in SUPPORTED_FILETYPES:
            return f'{extension} is not a supported filetype.'

        if attachment.size > ATTACHMENT_BYTES_MAX:
            megabytes = ATTACHMENT_BYTES_MAX // BYTES_PER_MEGABYTE
            return f'A sound must be smaller than {megabytes} MB.'

        if name is None:
            stem = path.stem
        else:
            stem = name

        sound_name = alphanumerical(stem).lower()

        if not sound_name:
            return 'A sound name must contain a letter or a number.'

        if RANDOM_SOUND in sound_name:
            return 'Please use another filename.'

        filename = f'{sound_name}{extension}'
        default_path = self.default_directory.joinpath(filename)
        member_path = self.member_directory.joinpath(filename)

        if member_path.exists() or default_path.exists():
            return f"'{sound_name}' already exists. Please use another filename."

        await download(self.viking.session, attachment.url, member_path)

        await self.sounds.create(sound_name, author_identifier)

        return f'Command was successfully added. Please use: ***play {sound_name}**'

    async def _sound_store_by_guild(
        self,
        guild_identifier: int,
        attachment: discord.Attachment,
        name: str | None,
        author_identifier: int
    ) -> str:
        if not await self.viking.update(guild_identifier):
            return 'This command can only be used in a configured server.'

        return await self._sound_store(attachment, name, author_identifier)

    async def cleanup(self, guild: Guild) -> None:
        voice_client = guild.voice_client

        if voice_client is not None:
            await voice_client.disconnect()

        player = self.players.pop(guild.id, None)

        if player is not None:
            player.cancel()

        self.views.pop(guild.id, None)

    def file_get(self, query: str) -> Path | None:
        sound_map = self._sound_map_build()
        return sound_map.get(query)

    def player_get(self, ctx: Context) -> Player:
        player = self.players.get(ctx.guild.id)

        if player is None:
            player = Player(ctx)
            self.players[ctx.guild.id] = player

            player.start()

        return player

    def sound_search(self, query: str) -> Path | None:
        sound_map = self._sound_map_build()

        if query in sound_map:
            return sound_map[query]

        match = process.extractOne(
            query,
            sound_map.keys(),
            score_cutoff=SOUND_MATCH_SCORE_MIN
        )

        if match:
            filename, *_ = match
            return sound_map.get(filename)

        return None

    def soundbank_get(self) -> list[Path]:
        return list(self.default_directory.iterdir()) + list(self.member_directory.iterdir())

    async def cog_unload(self) -> None:
        for player in list(self.players.values()):
            player.cancel()

        self.players.clear()
        self.views.clear()

    # Commands

    @commands.command()
    async def add(self, ctx: Context, *, name: str | None = None) -> None:
        """
        *add <filename>

        A command that adds a sound from a member.
        """

        if not ctx.message.attachments:
            return

        await ctx.typing()

        attachment = ctx.message.attachments[0]

        message = await self._sound_store(attachment, name, ctx.author.id)
        await ctx.send(message)

    @commands.hybrid_command(description='Add a tag to a sound.')
    @app_commands.describe(sound_name='The name of the sound.', tag='The tag to add.')
    @app_commands.autocomplete(sound_name=sound_autocomplete)
    async def addtag(self, ctx: Context, sound_name: str, *, tag: str) -> None:
        """
        *addtag <sound> <tag>

        A command that adds a tag to a sound.
        """

        await ctx.typing()

        tag_name = tag.lower().strip()

        row = await self.sounds.tags_row_get(sound_name)

        if row is None:
            message = f'**{sound_name}** was not found.'
            await ctx.send(message)

            return

        identifier, tags = row
        existing = tags or []

        if tag_name in existing:
            message = f'**{sound_name}** already has the tag **{tag_name}**.'
            await ctx.send(message)

            return

        await self.sounds.tag_append(identifier, tag_name)

        message = f'Tag **{tag_name}** added to **{sound_name}**.'
        await ctx.send(message)

    @commands.hybrid_command(description='Display an interactive soundbank.')
    async def browse(self, ctx: Context) -> None:
        """
        *browse

        A command that displays an interactive soundbank.
        """

        await ctx.typing()

        soundbank = self.soundbank_get()
        sounds = sorted(sound.stem for sound in soundbank)

        play_sound = partial(self._sound_play_by_name, ctx)

        view, content = audio_browser_create(ctx, sounds, play_sound)
        message = await ctx.send(content=content or None, view=view)
        view.message = message
        self.views[ctx.guild.id] = view

    @commands.hybrid_command(description='Connect to a voice channel.')
    @app_commands.describe(channel='The voice channel to connect to.')
    async def connect(
        self,
        ctx: Context,
        *,
        channel: discord.VoiceChannel | None = None
    ) -> None:
        """
        *connect <channel>

        A command that connects to a voice channel.
        """

        if channel is None:
            voice = ctx.author.voice

            if voice is None or voice.channel is None:
                message = 'You must be in a voice channel or specify one.'
                await ctx.send(message)

                return

            target = voice.channel
        else:
            target = channel

        if ctx.voice_client:
            if ctx.voice_client.channel.id == target.id:
                return

            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()

            await ctx.voice_client.disconnect()

        with contextlib.suppress(asyncio.TimeoutError):
            await target.connect()

    @commands.hybrid_command(description='Delete a sound you uploaded.')
    @app_commands.describe(query='The name of the sound to delete.')
    @app_commands.autocomplete(query=sound_autocomplete)
    async def delete(self, ctx: Context, query: str) -> None:
        """
        *delete <sound>

        A command that deletes the sound uploaded by the author.
        """

        await ctx.typing()

        if await self.sounds.owned_identifier_get(query, ctx.author.id) is None:
            message = f'You do not have permission to delete **{query}**.'
            await ctx.send(message)

            return

        file = self.file_get(query)

        if file is None:
            message = f'**{query}** was not found.'
            await ctx.send(message)

            return

        file.unlink(missing_ok=True)

        await self.sounds.delete(query)

        message = f'**{query}** was successfully deleted.'
        await ctx.send(message)

    @commands.hybrid_command(description='Display all sounds you have uploaded.')
    async def mysounds(self, ctx: Context) -> None:
        """
        *mysounds

        A command that displays all sounds uploaded by the author.
        """

        await ctx.typing()

        rows = await self.sounds.creator_names_get(ctx.author.id)

        sounds = sorted(rows)

        if not sounds:
            message = 'You have not uploaded any sounds.'
            await ctx.send(message)

            return

        play_sound = partial(self._sound_play_by_name, ctx)

        view, content = audio_browser_create(
            ctx,
            sounds,
            play_sound,
            placeholder='Select one of your sounds...',
            title='My Sounds'
        )

        message = await ctx.send(content=content or None, view=view)
        view.message = message
        self.views[ctx.guild.id] = view

    @commands.hybrid_command(description='Pause the current sound.')
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

    @commands.hybrid_command(description='Play a sound from the soundbank.')
    @app_commands.describe(query='The name of the sound to play.')
    @app_commands.autocomplete(query=sound_autocomplete)
    async def play(self, ctx: Context, *, query: str) -> None:
        """
        *play <sound>

        A command that plays a sound from the soundbank.
        """

        await ctx.typing()

        if query == RANDOM_SOUND:
            soundbank = self.soundbank_get()
            sound = self.viking.random.choice(soundbank)
        else:
            sound = self.sound_search(query)

        if sound is None:
            message = f"'{query}' could not be found."
            await ctx.send(message)

            return

        await self._sound_play(ctx, sound)

    @commands.hybrid_command(description='Remove a tag from a sound.')
    @app_commands.describe(sound_name='The name of the sound.', tag='The tag to remove.')
    @app_commands.autocomplete(sound_name=sound_autocomplete)
    async def removetag(self, ctx: Context, sound_name: str, *, tag: str) -> None:
        """
        *removetag <sound> <tag>

        A command that removes a tag from a sound.
        """

        await ctx.typing()

        tag_name = tag.lower().strip()

        row = await self.sounds.tags_row_get(sound_name)

        if row is None:
            message = f'**{sound_name}** was not found.'
            await ctx.send(message)

            return

        identifier, tags = row
        existing = tags or []

        if tag_name not in existing:
            message = f'**{sound_name}** does not have the tag **{tag_name}**.'
            await ctx.send(message)

            return

        await self.sounds.tag_remove(identifier, tag_name)

        message = f'Tag **{tag_name}** removed from **{sound_name}**.'
        await ctx.send(message)

    @commands.hybrid_command(description='Rename a sound you uploaded.')
    @app_commands.describe(before='The current name.', after='The new name.')
    @app_commands.autocomplete(before=sound_autocomplete)
    async def rename(self, ctx: Context, before: str, after: str) -> None:
        """
        *rename <before> <after>

        A command to rename a sound.
        """

        await ctx.typing()

        identifier = await self.sounds.owned_identifier_get(before, ctx.author.id)

        if identifier is None:
            message = f'You do not have permission to modify **{before}**.'
            await ctx.send(message)

            return

        file = self.file_get(before)

        if file is None:
            message = f'**{before}** was not found.'
            await ctx.send(message)

            return

        after_name = alphanumerical(after).lower()

        if not after_name:
            message = 'A sound name must contain a letter or a number.'
            await ctx.send(message)

            return

        if RANDOM_SOUND in after_name:
            message = 'Please use another name.'
            await ctx.send(message)

            return

        before_path = self.member_directory.joinpath(file.name)
        after_path = self.member_directory.joinpath(after_name + file.suffix)

        if after_path.exists():
            message = f"'{after_name}' already exists. Please use another name."
            await ctx.send(message)

            return

        default_path = self.default_directory.joinpath(after_name + file.suffix)

        if default_path.exists():
            message = f"'{after_name}' already exists. Please use another name."
            await ctx.send(message)

            return

        before_path.rename(after_path)

        await self.sounds.rename(identifier, after_name)

        message = f'{before} was successfully renamed to **{after_name}**.'
        await ctx.send(message)

    @commands.hybrid_command(description='Resume the current sound.')
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

    @commands.hybrid_command(description='Skip to the next sound in the queue.')
    async def skip(self, ctx: Context) -> None:
        """
        *skip

        A command that skips the current sound, and plays the next
        sound in the queue.
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return

        if not ctx.voice_client.is_playing():
            return

        ctx.voice_client.stop()

    @commands.hybrid_command(description='Display all sounds uploaded by a member.')
    @app_commands.describe(identifier='The member by name, nickname or ID.')
    @app_commands.autocomplete(identifier=member_autocomplete)
    async def soundsfrom(self, ctx: Context, *, identifier: str) -> None:
        """
        *soundsfrom <identifier>

        A command that displays all sounds uploaded by a
        specified member.
        """

        await ctx.typing()

        discord_id = await identifier_get(ctx, identifier)

        if discord_id is None:
            return

        member = await MemberRepository(self.viking.guild.session).record_get(discord_id)

        if member is None:
            message = 'Member not found.'
            await ctx.send(message)

            return

        display_name = member.display_name

        rows = await self.sounds.creator_names_get(discord_id)

        if not rows:
            message = f"{display_name} hasn't uploaded a sound."
            await ctx.send(message)

            return

        sounds = sorted(rows)

        play_sound = partial(self._sound_play_by_name, ctx)

        view, content = audio_browser_create(
            ctx,
            sounds,
            play_sound,
            placeholder=f'Pick a {display_name} sound...',
            title=f"{display_name}'s Sounds"
        )

        message = await ctx.send(content=content or None, view=view)
        view.message = message
        self.views[ctx.guild.id] = view

    @commands.hybrid_command(description='Stop the current sound and clear the queue.')
    async def stop(self, ctx: Context) -> None:
        """
        *stop

        A command that stops the current sound, and removes all
        sounds from the queue.
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return

        await self.cleanup(ctx.guild)

    @commands.hybrid_command(description='Display the tags for a sound.')
    @app_commands.describe(sound_name='The name of the sound.')
    @app_commands.autocomplete(sound_name=sound_autocomplete)
    async def tags(self, ctx: Context, *, sound_name: str) -> None:
        """
        *tags <sound>

        A command that displays the tags for a sound.
        """

        await ctx.typing()

        tags = await self.sounds.tags_get(sound_name)

        if tags is None:
            message = f'**{sound_name}** was not found or has no tags.'
            await ctx.send(message)

            return

        if not tags:
            message = f'**{sound_name}** has no tags.'
            await ctx.send(message)

            return

        tag_list = ', '.join(sorted(tags))
        message = f'Tags for **{sound_name}**: {tag_list}'
        await ctx.send(message)

    @commands.hybrid_command(description='Display sound themes to browse.')
    async def themes(self, ctx: Context) -> None:
        """
        *themes

        A command that displays sound themes/categories to browse.
        """

        await ctx.typing()

        rows = await self.sounds.tagged_get()

        themes: dict[str, list[str]] = {}

        for name, tags in rows:
            if not tags:
                continue

            for tag in tags:
                themes.setdefault(tag, []).append(name)

        if not themes:
            message = 'No themes found. Add tags to sounds using `*addtag`.'
            await ctx.send(message)

            return

        view, content = theme_browser_create(ctx, themes)
        message = await ctx.send(content=content or None, view=view)
        view.message = message

        await view.wait()

        selected_theme = view.selected_item

        if selected_theme is None:
            return

        with contextlib.suppress(discord.HTTPException):
            await message.delete()

        sounds = sorted(themes[selected_theme])

        play_sound = partial(self._sound_play_by_name, ctx)

        sound_view, sound_content = audio_browser_create(
            ctx,
            sounds,
            play_sound,
            placeholder=f'Pick a {selected_theme} sound...',
            title=selected_theme
        )

        sound_message = await ctx.send(content=sound_content or None, view=sound_view)
        sound_view.message = sound_message
        self.views[ctx.guild.id] = sound_view

    @app_commands.command(description='Add a sound to the soundbank.')
    @app_commands.guild_only()
    async def upload(self, interaction: discord.Interaction) -> None:
        """
        /upload

        A command that opens a modal with a file picker to add a sound
        to the soundbank.
        """

        store = partial(self._sound_store_by_guild, interaction.guild_id)

        modal = SoundUploadModal(store)
        await interaction.response.send_modal(modal)


async def setup(viking: Viking) -> None:
    audio = Audio(viking)
    await viking.add_cog(audio)
