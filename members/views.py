from __future__ import annotations

import discord

from typing_extensions import TYPE_CHECKING

from core.limits import SELECT_DESCRIPTION_LENGTH_MAX, SELECT_LABEL_LENGTH_MAX
from core.views import AuthorView

if TYPE_CHECKING:
    from typing_extensions import Any

    from discord import Interaction
    from sqlalchemy import Row


MEMBER_SELECT_TIMEOUT_SECONDS = 15.0


class MemberSelect(discord.ui.Select['MemberSelectView']):
    def __init__(self, rows: list[Row[Any]]) -> None:
        options = [
            discord.SelectOption(
                label=row.display_name[:SELECT_LABEL_LENGTH_MAX],
                description=(
                    (row.name or row.nickname or '')[:SELECT_DESCRIPTION_LENGTH_MAX] or None
                ),
                value=str(row.discord_id)
            )
            for row in rows
        ]

        super().__init__(
            options=options,
            placeholder='Select a member...'
        )

    async def callback(self, interaction: Interaction) -> None:
        view = self.view
        view.selected_identifier = int(self.values[0])
        view.stop()

        await interaction.response.edit_message(
            content='Member selected.',
            view=None
        )


class MemberSelectView(AuthorView):
    def __init__(self, author_identifier: int, rows: list[Row[Any]]) -> None:
        super().__init__(author_identifier, timeout=MEMBER_SELECT_TIMEOUT_SECONDS)

        self.selected_identifier: int | None = None

        self.add_item(MemberSelect(rows))
