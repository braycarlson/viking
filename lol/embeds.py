from __future__ import annotations

import discord

from typing_extensions import TYPE_CHECKING

from core.text import list_format
from lol.api import ASSET
from lol.enums import Side

if TYPE_CHECKING:
    from typing_extensions import Any

    from core.db.lol import Champion, Spell
    from lol.models import Summoner


def _attribute_format(base: Any, per_level: Any) -> str:
    return f'{base} (+{per_level} per level)'


def build_embed(champion: str, build: dict[str, Any], colour: discord.Colour) -> discord.Embed:
    embed = discord.Embed(
        colour=colour,
        title=f'Recommended Items for {champion}'
    )

    embed.set_thumbnail(url='attachment://thumbnail.png')

    blocks = {
        key: value
        for key, value in build.items()
        if value
    }

    for key, value in blocks.items():
        items = list_format(value, symbol='bullet', sort=False)

        embed.add_field(
            inline=False,
            name=key,
            value=items
        )

    return embed


def champion_embed(champion: Champion, colour: discord.Colour) -> discord.Embed:
    embed = discord.Embed(
        colour=colour,
        title=champion.name
    )

    embed.set_thumbnail(url='attachment://thumbnail.png')

    stats = [
        ('Health', _attribute_format(champion.health, champion.health_per_level)),
        (
            'Health Regeneration',
            _attribute_format(champion.health_regeneration, champion.health_regeneration_per_level),
        ),
        ('Mana', _attribute_format(champion.mana, champion.mana_per_level)),
        (
            'Mana Regeneration',
            _attribute_format(champion.mana_regeneration, champion.mana_regeneration_per_level),
        ),
        ('Armor', _attribute_format(champion.armor, champion.armor_per_level)),
        ('Movement Speed', champion.movement_speed),
        ('Attack Range', champion.attack_range),
        (
            'Attack Damage',
            _attribute_format(champion.attack_damage, champion.attack_damage_per_level),
        ),
        (
            'Attack Speed',
            _attribute_format(champion.attack_speed, champion.attack_speed_per_level),
        ),
        (
            'Critical Strike',
            _attribute_format(champion.critical_strike, champion.critical_strike_per_level),
        ),
    ]

    for name, value in stats:
        embed.add_field(inline=False, name=name, value=value)

    return embed


def game_embeds(
    mode: str | None,
    entries: list[tuple[int, str, str]]
) -> tuple[discord.Embed, discord.Embed, discord.Embed]:
    main = discord.Embed(
        title='Game',
        description=f'{mode}'
    )
    blue = discord.Embed(
        title='Blue Team',
        colour=discord.Colour.blue()
    )
    red = discord.Embed(
        title='Red Team',
        colour=discord.Colour.red()
    )

    for team, name, placement in entries:
        if team == Side.BLUE:
            blue.add_field(
                inline=False,
                name=name,
                value=placement
            )

        if team == Side.RED:
            red.add_field(
                inline=False,
                name=name,
                value=placement
            )

    return main, blue, red


def rune_embed(champion_name: str) -> discord.Embed:
    embed = discord.Embed(title=f'Runepage for {champion_name}')
    embed.set_thumbnail(url='attachment://thumbnail.png')
    embed.set_image(url='attachment://runepage.png')

    return embed


def skill_embed(champion_name: str) -> discord.Embed:
    embed = discord.Embed(title=f'Skill Order for {champion_name}')
    embed.set_thumbnail(url='attachment://thumbnail.png')
    embed.set_image(url='attachment://skillorder.png')

    return embed


def spell_embed(spell: Spell, version: str | None, colour: discord.Colour) -> discord.Embed:
    embed = discord.Embed(colour=colour)

    embed.set_thumbnail(
        url=f'{ASSET}/cdn/{version}/img/spell/{spell.full_image}'
    )

    embed.add_field(inline=False, name='Name', value=spell.name)
    embed.add_field(inline=False, name='Description', value=spell.description)
    embed.add_field(inline=False, name='Acquired', value=f'Level {spell.level}')
    embed.add_field(inline=False, name='Range', value=f'{spell.spell_range} units')
    embed.add_field(inline=False, name='Cooldown', value=f'{spell.cooldown} seconds')

    return embed


def summoner_embed(
    summoner: Summoner,
    placement: str,
    champions: str,
    colour: discord.Colour
) -> discord.Embed:
    embed = discord.Embed(
        title=f'{summoner.name} (Level {summoner.level})',
        colour=colour
    )

    embed.add_field(inline=False, name='Placement', value=placement)
    embed.add_field(inline=False, name='Champions', value=champions)

    return embed
