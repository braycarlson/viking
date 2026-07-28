from __future__ import annotations

import contextlib

import discord

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing_extensions import TYPE_CHECKING

from core.limits import SELECT_LABEL_LENGTH_MAX, SELECT_OPTIONS_MAX
from core.views import AuthorView

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing_extensions import Any

    from discord import Interaction


class PageSizeError(ValueError):
    pass


@dataclass
class PaginatorConfiguration:
    delete_message_on_timeout: bool = False
    per_page: int = SELECT_OPTIONS_MAX
    placeholder: str = 'Select an item...'
    return_on_selection: bool = False
    timeout: float = 180.0


class PageProvider(ABC):
    @abstractmethod
    def page_get(self, page: int) -> list[Any]:
        raise NotImplementedError

    @abstractmethod
    def total_items_get(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def total_pages_get(self) -> int:
        raise NotImplementedError


class SelectionHandler(ABC):
    @abstractmethod
    async def on_select(
        self,
        interaction: Interaction,
        view: PaginatorView,
        item: Any,
        index: int
    ) -> None:
        raise NotImplementedError


class ListPageProvider(PageProvider):
    def __init__(self, items: list[Any], per_page: int) -> None:
        if per_page < 1 or per_page > SELECT_OPTIONS_MAX:
            message = (
                f'per_page must be between 1 and '
                f'{SELECT_OPTIONS_MAX}: {per_page}'
            )

            raise PageSizeError(message)

        self.items = items
        self.per_page = per_page
        self._total_pages = -(-len(items) // per_page)

    def page_get(self, page: int) -> list[Any]:
        if page < 1 or page > self._total_pages:
            return []

        base = (page - 1) * self.per_page
        return self.items[base:base + self.per_page]

    def total_items_get(self) -> int:
        return len(self.items)

    def total_pages_get(self) -> int:
        return self._total_pages


class ItemSelect(discord.ui.Select['PaginatorView']):
    def __init__(
        self,
        items: list[Any],
        *,
        item_format: Callable[[Any], str] | None = None,
        placeholder: str = 'Select an item...'
    ) -> None:
        self.item_format = item_format or str
        self.items = items[:SELECT_OPTIONS_MAX]

        options = [
            discord.SelectOption(
                label=self.item_format(item)[:SELECT_LABEL_LENGTH_MAX],
                value=str(index)
            )
            for index, item in enumerate(self.items)
        ]

        super().__init__(
            options=options,
            placeholder=placeholder,
            row=0
        )

    async def callback(self, interaction: Interaction) -> None:
        index = int(self.values[0])
        item = self.items[index]

        view = self.view
        view.selected_item = item
        view.selected_index = index

        if view.selection_handler is not None:
            await view.selection_handler.on_select(interaction, view, item, index)
            return

        if view.configuration.return_on_selection:
            view.stop()

        await interaction.response.defer()


class PaginatorView(AuthorView):
    def __init__(
        self,
        author_identifier: int,
        provider: PageProvider,
        *,
        configuration: PaginatorConfiguration | None = None,
        item_format: Callable[[Any], str] | None = None,
        selection_handler: SelectionHandler | None = None
    ) -> None:
        self.configuration = configuration or PaginatorConfiguration()

        super().__init__(author_identifier, timeout=self.configuration.timeout)

        self.current_page = 1
        self.item_format = item_format
        self.provider = provider
        self.selected_index: int | None = None
        self.selected_item: Any | None = None
        self.selection_handler = selection_handler

        self._view_update()

    def _view_update(self) -> None:
        self.clear_items()

        items = self.provider.page_get(self.current_page)

        select = ItemSelect(
            items,
            item_format=self.item_format,
            placeholder=self.configuration.placeholder
        )
        self.add_item(select)

        total_pages = self.provider.total_pages_get()

        if total_pages > 1:
            self.add_item(PreviousPageButton(disabled=self.current_page == 1))
            self.add_item(NextPageButton(disabled=self.current_page >= total_pages))

        self.add_item(CloseButton())

    def content_get(self) -> str:
        total_pages = self.provider.total_pages_get()

        if total_pages > 1:
            return f'Page {self.current_page} of {total_pages}'

        return ''

    async def on_timeout(self) -> None:
        if self.message is None:
            return

        if self.configuration.delete_message_on_timeout:
            with contextlib.suppress(discord.HTTPException):
                await self.message.delete()
        else:
            with contextlib.suppress(discord.HTTPException):
                message = 'Menu timed out.'
                await self.message.edit(content=message, view=None)

    async def page_show(self, interaction: Interaction, page: int) -> None:
        self.current_page = page
        self._view_update()

        await interaction.response.edit_message(
            content=self.content_get(),
            view=self
        )


class CloseButton(discord.ui.Button[PaginatorView]):
    def __init__(self, *, label: str = 'Close', row: int = 2) -> None:
        super().__init__(
            label=label,
            row=row,
            style=discord.ButtonStyle.danger
        )

    async def callback(self, interaction: Interaction) -> None:
        view = self.view
        view.stop()

        message = 'Menu closed.'
        await interaction.response.edit_message(content=message, view=None)


class NextPageButton(discord.ui.Button[PaginatorView]):
    def __init__(self, *, disabled: bool = False, label: str = 'Next Page', row: int = 1) -> None:
        super().__init__(
            disabled=disabled,
            label=label,
            row=row,
            style=discord.ButtonStyle.secondary
        )

    async def callback(self, interaction: Interaction) -> None:
        view = self.view
        await view.page_show(interaction, view.current_page + 1)


class PreviousPageButton(discord.ui.Button[PaginatorView]):
    def __init__(
        self,
        *,
        disabled: bool = False,
        label: str = 'Previous Page',
        row: int = 1
    ) -> None:
        super().__init__(
            disabled=disabled,
            label=label,
            row=row,
            style=discord.ButtonStyle.secondary
        )

    async def callback(self, interaction: Interaction) -> None:
        view = self.view
        await view.page_show(interaction, view.current_page - 1)
