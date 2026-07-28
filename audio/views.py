from __future__ import annotations

import discord

from typing_extensions import TYPE_CHECKING

from core.limits import SELECT_OPTIONS_MAX
from core.pagination import (
    CloseButton,
    ItemSelect,
    ListPageProvider,
    NextPageButton,
    PaginatorConfiguration,
    PaginatorView,
    PreviousPageButton,
    SelectionHandler,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from typing_extensions import Any

    from discord import Interaction
    from discord.ext.commands import Context


BLANK = '\u2800'
BROWSER_TIMEOUT_SECONDS = 300.0
LABEL_WIDTH = 28

GLYPH_WIDTH = {
    ' ': 0.35,
    'f': 0.4,
    'i': 0.35,
    'j': 0.35,
    'l': 0.35,
    'm': 0.95,
    'r': 0.4,
    't': 0.4,
    'w': 0.9,
}
LOWERCASE_WIDTH = 0.6
UPPERCASE_WIDTH = 0.75


def _glyph_width(character: str) -> float:
    if character in GLYPH_WIDTH:
        return GLYPH_WIDTH[character]

    if character.isupper():
        return UPPERCASE_WIDTH

    return LOWERCASE_WIDTH


def _label_pad(label: str, width: int) -> str:
    blanks = round(width - sum(_glyph_width(character) for character in label))

    if blanks <= 0:
        return label

    left = blanks // 2
    right = blanks - left

    return f'{BLANK * left}{label}{BLANK * right}'


class AudioControlView(PaginatorView):
    def __init__(
        self,
        ctx: Context,
        provider: ListPageProvider,
        *,
        configuration: PaginatorConfiguration | None = None,
        item_format: Callable[[Any], str] | None = None,
        selection_handler: SelectionHandler | None = None,
        title: str = 'Soundbank'
    ) -> None:
        if configuration:
            placeholder = configuration.placeholder
        else:
            placeholder = 'Select a sound to play...'

        self.ctx = ctx
        self.default_placeholder = placeholder
        self.now_playing: str | None = None
        self.play_pause_button: PlayPauseButton | None = None
        self.title = title

        super().__init__(
            ctx.author.id,
            provider,
            configuration=configuration,
            item_format=item_format,
            selection_handler=selection_handler
        )

    def _placeholder_get(self) -> str:
        if self.now_playing:
            return f'Now playing: {self.now_playing}'

        return self.default_placeholder

    def _view_update(self) -> None:
        self.clear_items()

        items = self.provider.page_get(self.current_page)

        select = ItemSelect(
            items,
            item_format=self.item_format,
            placeholder=self._placeholder_get()
        )
        self.add_item(select)

        total_pages = self.provider.total_pages_get()
        self.play_pause_button = PlayPauseButton(self.ctx)

        rows = []

        if total_pages > 1:
            previous_button = PreviousPageButton(
                disabled=self.current_page == 1,
                label=_label_pad('Previous Page', LABEL_WIDTH)
            )

            next_button = NextPageButton(
                disabled=self.current_page >= total_pages,
                label=_label_pad('Next Page', LABEL_WIDTH)
            )

            pagination = [previous_button, next_button]
            rows.append(pagination)

        playback = [self.play_pause_button, SkipButton(self.ctx)]
        rows.append(playback)

        close_button = CloseButton(label=_label_pad('Close', LABEL_WIDTH))

        session = [close_button, DisconnectButton(self.ctx)]
        rows.append(session)

        for index, row in enumerate(rows, start=1):
            for button in row:
                button.row = index
                self.add_item(button)

    def content_get(self) -> str:
        total_pages = self.provider.total_pages_get()

        if total_pages > 1:
            return f'{self.title}: Page {self.current_page} of {total_pages}'

        return self.title

    def now_playing_clear(self) -> None:
        self.now_playing = None
        self.play_pause_reset()
        self._view_update()

    def now_playing_set(self, name: str) -> None:
        self.now_playing = name

        if self.play_pause_button is not None:
            self.play_pause_button.label = _label_pad('Pause', LABEL_WIDTH)
            self.play_pause_button.style = discord.ButtonStyle.secondary

        self._view_update()

    async def page_show(self, interaction: Interaction, page: int) -> None:
        self.current_page = page
        self._view_update()

        await interaction.response.edit_message(
            content=self.content_get(),
            view=self
        )

    def play_pause_reset(self) -> None:
        if self.play_pause_button is not None:
            self.play_pause_button.label = _label_pad('Play', LABEL_WIDTH)
            self.play_pause_button.style = discord.ButtonStyle.success


class AudioSelectionHandler(SelectionHandler):
    def __init__(self, play_callback: Callable[..., Awaitable[None]]) -> None:
        self.play_callback = play_callback

    async def on_select(
        self,
        interaction: Interaction,
        view: AudioControlView,
        item: Any,
        index: int  # noqa: ARG002
    ) -> None:
        view.now_playing_set(item)
        await interaction.response.edit_message(view=view)
        await self.play_callback(item)


class DisconnectButton(discord.ui.Button['AudioControlView']):
    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx

        super().__init__(
            label=_label_pad('Disconnect', LABEL_WIDTH),
            style=discord.ButtonStyle.danger
        )

    async def callback(self, interaction: Interaction) -> None:
        view = self.view

        if self.ctx.voice_client:
            await self.ctx.voice_client.disconnect()

        view.now_playing_clear()
        await interaction.response.edit_message(view=view)


class PlayPauseButton(discord.ui.Button['AudioControlView']):
    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx

        super().__init__(
            label=_label_pad('Play', LABEL_WIDTH),
            style=discord.ButtonStyle.success
        )

    async def callback(self, interaction: Interaction) -> None:
        voice_client = self.ctx.voice_client

        if voice_client:
            paused = voice_client.is_paused()
            playing = voice_client.is_playing()

            if paused:
                voice_client.resume()
                self.label = _label_pad('Pause', LABEL_WIDTH)
                self.style = discord.ButtonStyle.secondary

            if playing:
                voice_client.pause()
                self.label = _label_pad('Play', LABEL_WIDTH)
                self.style = discord.ButtonStyle.success

        await interaction.response.edit_message(view=self.view)


class SkipButton(discord.ui.Button['AudioControlView']):
    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx

        super().__init__(
            label=_label_pad('Skip', LABEL_WIDTH),
            style=discord.ButtonStyle.secondary
        )

    async def callback(self, interaction: Interaction) -> None:
        view = self.view

        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.stop()

        view.now_playing_clear()
        await interaction.response.edit_message(view=view)


def audio_browser_create(
    ctx: Context,
    sounds: list[str],
    play_callback: Callable[..., Awaitable[None]],
    *,
    placeholder: str = 'Select a sound to play...',
    title: str = 'Soundbank'
) -> tuple[AudioControlView, str]:
    configuration = PaginatorConfiguration(
        per_page=SELECT_OPTIONS_MAX,
        placeholder=placeholder,
        timeout=BROWSER_TIMEOUT_SECONDS
    )

    provider = ListPageProvider(sounds, configuration.per_page)
    handler = AudioSelectionHandler(play_callback)

    view = AudioControlView(
        ctx,
        provider,
        configuration=configuration,
        selection_handler=handler,
        title=title
    )

    return view, view.content_get()


def theme_browser_create(
    ctx: Context,
    themes: dict[str, list[str]],
    *,
    placeholder: str = 'Select a theme...'
) -> tuple[PaginatorView, str]:
    configuration = PaginatorConfiguration(
        per_page=SELECT_OPTIONS_MAX,
        placeholder=placeholder,
        return_on_selection=True,
        timeout=BROWSER_TIMEOUT_SECONDS
    )

    theme_names = sorted(themes.keys())
    provider = ListPageProvider(theme_names, configuration.per_page)

    def theme_format(theme: str) -> str:
        count = len(themes[theme])
        return f'{theme} ({count})'

    view = PaginatorView(
        ctx.author.id,
        provider,
        configuration=configuration,
        item_format=theme_format
    )

    total_pages = provider.total_pages_get()

    if total_pages > 1:
        content = f'Themes: Page 1 of {total_pages}'
    else:
        content = 'Themes'

    return view, content
