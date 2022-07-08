import discord

from utilities.format import format_list
from utilities.pagination import Pages


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
