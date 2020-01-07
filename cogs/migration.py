from database.model import (
    ActiveMembers,
    database,
    GuildRoles,
    HiddenCommands,
    LoLChampions,
    LoLSpells,
    NHLTeams,
    NHLPlayers,
    PublicCommands
)
from discord.ext import commands
from utilities.lol import (
    Champion,
    Spell,
    get_champions,
    get_spells,
    get_spell_version
)
from utilities.nhl import (
    Player,
    Team,
    get_player,
    get_teams,
    get_team_roster,
)


class Migration(commands.Cog):
    def __init__(self, viking):
        self.viking = viking
        self.session = viking.session

    async def insert_roles(self):
        for guild in self.viking.guilds:
            for role in guild.roles:
                await GuildRoles.create(
                    id=role.id,
                    name=role.name,
                    colour=str(role.colour),
                    hoist=role.hoist,
                    position=role.position,
                    managed=role.managed,
                    mentionable=role.mentionable,
                    is_default=role.is_default(),
                    created_at=role.created_at
                )

    async def insert_public_commands(self):
        for viking_commands in self.viking.commands:
            if not viking_commands.hidden:
                await PublicCommands.create(name=viking_commands.name)

                if viking_commands.aliases:
                    for alias in viking_commands.aliases:
                        await PublicCommands.update.values(
                                aliases=database.func.array_prepend(
                                    alias,
                                    PublicCommands.aliases
                                )
                            ).where(PublicCommands.name == viking_commands.name).gino.status()

    async def insert_hidden_commands(self):
        for viking_commands in self.viking.commands:
            if viking_commands.hidden:
                await HiddenCommands.create(name=viking_commands.name)

                if viking_commands.aliases:
                    for alias in viking_commands.aliases:
                        await HiddenCommands.update.values(
                                aliases=database.func.array_prepend(
                                    alias,
                                    HiddenCommands.aliases
                                )
                            ).where(HiddenCommands.name == viking_commands.name).gino.status()

    async def insert_members(self):
        for guild in self.viking.guilds:
            for member in guild.members:
                await ActiveMembers.create(
                    discord_id=member.id,
                    name=member.name,
                    discriminator=member.discriminator,
                    display_name=member.display_name,
                    nickname=member.nick,
                    role_id=member.top_role.id,
                    bot=member.bot,
                    created_at=member.created_at,
                    joined_at=member.joined_at
                )

    async def insert_nhl_teams(self):
        teams = await get_teams(self.session)

        for team in teams.get('teams'):
            team = Team(team)

            await NHLTeams.create(
                team_id=team.id,
                name=team.name,
                link=team.link,
                venue_id=team.venue_id,
                venue_name=team.venue_name,
                venue_link=team.venue_link,
                venue_city=team.venue_city,
                timezone_id=team.timezone_id,
                timezone_offset=team.timezone_offset,
                timezone_tz=team.timezone_tz,
                abbreviation=team.abbreviation,
                team_name=team.team_name,
                location_name=team.location_name,
                first_year_of_play=team.first_year_of_play,
                division_id=team.division_id,
                division_name=team.division_name,
                division_name_short=team.division_name_short,
                division_link=team.division_link,
                division_abbreviation=team.division_abbreviation,
                conference_id=team.conference_id,
                conference_name=team.conference_name,
                conference_link=team.conference_link,
                franchise_id=team.franchise_id,
                franchise_name=team.franchise_name,
                franchise_link=team.franchise_link,
                short_name=team.short_name,
                official_website=team.official_website,
                active=team.active
            )

    async def insert_nhl_players(self):
        teams = await NHLTeams.select('team_id').gino.all()

        for team in teams:
            team_id = dict(team).get('team_id')
            rosters = await get_team_roster(self.session, team_id)

            for roster in rosters.get('roster'):
                player_id = roster.get('person').get('id')
                players = await get_player(self.session, player_id)

                for player in players.get('people'):
                    player = Player(player)

                    await NHLPlayers.create(
                        player_id=player.id,
                        full_name=player.full_name,
                        link=player.link,
                        first_name=player.first_name,
                        last_name=player.last_name,
                        number=player.number,
                        birthdate=player.birthdate,
                        age=player.age,
                        city=player.city,
                        province=player.province,
                        country=player.country,
                        nationality=player.nationality,
                        height=player.height,
                        weight=player.weight,
                        active=player.active,
                        alternate_captain=player.alternate_captain,
                        captain=player.captain,
                        rookie=player.rookie,
                        shooting_hand=player.shooting_hand,
                        team_id=player.team_id,
                        team_name=player.team_name,
                        team_link=player.team_link,
                        position_code=player.position_code,
                        position_name=player.position_name,
                        position_type=player.position_type,
                        position_abbreviation=player.position_abbreviation,
                    )

    async def insert_lol_champions(self):
        version = await get_spell_version(self.session)
        champions = await get_champions(self.session, version)

        for champion in champions.get('data').values():
            champion = Champion(champion)

            await LoLChampions.create(
                champion_id=champion.key,
                name=champion.name,
                title=champion.title,
                blurb=champion.blurb,
                attack_information=champion.attack_information,
                defense_information=champion.defense_information,
                magic_information=champion.magic_information,
                difficulty_information=champion.difficulty_information,
                full_image=champion.full_image,
                champion_class=champion.champion_class,
                resource=champion.resource,
                health=champion.health,
                health_per_level=champion.health_per_level,
                mana=champion.mana,
                mana_per_level=champion.mana_per_level,
                movement_speed=champion.movement_speed,
                armor=champion.armor,
                armor_per_level=champion.armor_per_level,
                spellblock=champion.spellblock,
                spellblock_per_level=champion.spellblock_per_level,
                attack_range=champion.attack_range,
                health_regeneration=champion.health_regeneration,
                health_regeneration_per_level=champion.health_regeneration_per_level,
                mana_regeneration=champion.mana_regeneration,
                mana_regeneration_per_level=champion.mana_regeneration_per_level,
                critical_strike=champion.critical_strike,
                critical_strike_per_level=champion.critical_strike_per_level,
                attack_damage=champion.attack_damage,
                attack_damage_per_level=champion.attack_damage_per_level,
                attack_speed_per_level=champion.attack_speed_per_level,
                attack_speed=champion.attack_speed
            )

    async def insert_lol_spells(self):
        version = await get_spell_version(self.session)
        spells = await get_spells(self.session, version)

        for spell in spells.get('data').values():
            spell = Spell(spell)

            await LoLSpells.create(
                spell_id=spell.key,
                spell_key=spell.id,
                name=spell.name,
                description=spell.description,
                maximum_rank=spell.maximum_rank,
                cooldown=spell.cooldown,
                cost=spell.cost,
                cost_type=spell.cost_type,
                maximum_ammo=spell.maximum_ammo,
                spell_range=spell.spell_range,
                full_image=spell.full_image,
                resource=spell.resource,
                level=spell.level
            )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def drop(self, ctx):
        """
        *drop <table>

        A command that drops all tables in the database.
        """

        await ctx.message.delete()
        await database.gino.drop_all()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def run(self, ctx):
        """
        *run

        A command that executes the necessary queries to create the
        database.
        """

        await ctx.message.delete()

        await database.gino.create_all()
        await self.insert_public_commands()
        await self.insert_hidden_commands()
        await self.insert_roles()
        await self.insert_members()
        await self.insert_nhl_teams()
        await self.insert_nhl_players()
        await self.insert_lol_champions()
        await self.insert_lol_spells()


def setup(viking):
    viking.add_cog(Migration(viking))
