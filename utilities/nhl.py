import discord
from asyncio import TimeoutError
from database.model import NHLTeams, NHLPlayers
from datetime import datetime
from rapidfuzz import process
from utilities.format import format_list
from utilities.request import fetch


class Game:
    __slots__ = (
        'status',
        'home_id',
        'home_name',
        'home_score',
        'home_wins',
        'home_losses',
        'home_overtime',
        'away_id',
        'away_name',
        'away_score',
        'away_wins',
        'away_losses',
        'away_overtime',
        'venue_id',
        'venue_name',
    )

    def __init__(self, data):
        self.status = data.get('status').get('abstractGameState')
        self.home_id = data.get('teams').get('home').get('team').get('id')
        self.home_name = data.get('teams').get('home').get('team').get('name')
        self.home_score = data.get('teams').get('home').get('score')
        self.home_wins = data.get('teams').get('home').get('leagueRecord').get('wins')
        self.home_losses = data.get('teams').get('home').get('leagueRecord').get('losses')
        self.home_overtime = data.get('teams').get('home').get('leagueRecord').get('ot')
        self.away_id = data.get('teams').get('away').get('team').get('id')
        self.away_name = data.get('teams').get('away').get('team').get('name')
        self.away_score = data.get('teams').get('away').get('score')
        self.away_wins = data.get('teams').get('away').get('leagueRecord').get('wins')
        self.away_losses = data.get('teams').get('away').get('leagueRecord').get('losses')
        self.away_overtime = data.get('teams').get('away').get('leagueRecord').get('ot')
        self.venue_id = data.get('venue').get('id')
        self.venue_name = data.get('venue').get('name')

    @property
    def home_team_record(self):
        return f"{self.home_wins}-{self.home_losses}-{self.home_overtime}"

    @property
    def away_team_record(self):
        return f"{self.away_wins}-{self.away_losses}-{self.away_overtime}"

    @property
    def winner(self):
        if self.status != 'Final':
            return None

        if self.home_score > self.away_score:
            return self.home_name

        if self.away_score > self.home_score:
            return self.away_name


class GoalieSingleSeason:
    __slots__ = (
        'time_on_ice',
        'overtime',
        'shutouts',
        'ties',
        'wins',
        'losses',
        'saves',
        'power_play_saves',
        'short_handed_saves',
        'even_saves',
        'short_handed_shots',
        'even_shots',
        'power_play_shots',
        'save_percentage',
        'goal_against_average',
        'games',
        'games_started',
        'shots_against',
        'goals_against',
        'time_on_ice_per_game',
        'power_play_save_percentage',
        'short_handed_save_percentage',
        'even_strength_save_percentage'
    )

    def __init__(self, data):
        self.time_on_ice = data.get('timeOnIce')
        self.overtime = data.get('ot')
        self.shutouts = data.get('shutouts')
        self.ties = data.get('ties')
        self.wins = data.get('wins')
        self.losses = data.get('losses')
        self.saves = data.get('saves')
        self.power_play_saves = data.get('powerPlaySaves')
        self.short_handed_saves = data.get('shortHandedSaves')
        self.even_saves = data.get('evenSaves')
        self.short_handed_shots = data.get('shortHandedShots')
        self.even_shots = data.get('evenShots')
        self.power_play_shots = data.get('powerPlayShots')
        self.save_percentage = data.get('savePercentage')
        self.goal_against_average = data.get('goalAgainstAverage')
        self.games = data.get('games')
        self.games_started = data.get('gamesStarted')
        self.shots_against = data.get('shotsAgainst')
        self.goals_against = data.get('goalsAgainst')
        self.time_on_ice_per_game = data.get('timeOnIcePerGame')
        self.power_play_save_percentage = data.get('powerPlaySavePercentage')
        self.short_handed_save_percentage = data.get('shortHandedSavePercentage')
        self.even_strength_save_percentage = data.get('evenStrengthSavePercentage')


class Player:
    __slots__ = (
        'id',
        'full_name',
        'link',
        'first_name',
        'last_name',
        'number',
        'birthdate',
        'age',
        'city',
        'province',
        'country',
        'nationality',
        'height',
        'weight',
        'active',
        'alternate_captain',
        'captain',
        'rookie',
        'shooting_hand',
        'team_id',
        'team_name',
        'team_link',
        'position_code',
        'position_name',
        'position_type',
        'position_abbreviation'
    )

    def __init__(self, data):
        self.id = data.get('id')
        self.full_name = data.get('fullName')
        self.link = data.get('link')
        self.first_name = data.get('firstName')
        self.last_name = data.get('lastName')
        self.number = data.get('primaryNumber')
        self.birthdate = data.get('birthDate')
        self.age = data.get('currentAge')
        self.city = data.get('birthCity')
        self.province = data.get('birthStateProvince')
        self.country = data.get('birthCountry')
        self.nationality = data.get('nationality')
        self.height = data.get('height')
        self.weight = data.get('weight')
        self.active = data.get('active')
        self.alternate_captain = data.get('alternateCaptain')
        self.captain = data.get('captain')
        self.rookie = data.get('rookie')
        self.shooting_hand = data.get('shootsCatches')
        self.team_id = data.get('currentTeam').get('id')
        self.team_name = data.get('currentTeam').get('name')
        self.team_link = data.get('currentTeam').get('link')
        self.position_code = data.get('primaryPosition').get('code')
        self.position_name = data.get('primaryPosition').get('name')
        self.position_type = data.get('primaryPosition').get('type')
        self.position_abbreviation = data.get('primaryPosition').get('abbreviation')

    @property
    def birthday(self):
        return datetime.strptime(self.birthdate, '%Y-%m-%d').strftime('%B %d, %Y')


class PlayerSingleSeason:
    __slots__ = (
        'time_on_ice',
        'assists',
        'goals',
        'pim',
        'shots',
        'games',
        'hits',
        'powerplay_goals',
        'powerplay_points',
        'powerplay_time_on_ice',
        'even_time_on_ice',
        'penalty_minutes',
        'faceoff_percentage',
        'shot_percentage',
        'game_winning_goals',
        'overtime_goals',
        'shorthanded_goals',
        'shorthanded_points',
        'shorthanded_time_on_ice',
        'blocked',
        'plus_minus',
        'points',
        'shifts',
        'time_on_ice_per_game',
        'even_time_on_ice_per_game',
        'short_handed_time_on_ice_per_game',
        'power_play_time_on_ice_per_game'
    )

    def __init__(self, data):
        self.time_on_ice = data.get('timeOnIce')
        self.assists = data.get('assists')
        self.goals = data.get('goals')
        self.pim = data.get('pim')
        self.shots = data.get('shots')
        self.games = data.get('games')
        self.hits = data.get('hits')
        self.powerplay_goals = data.get('powerPlayGoals')
        self.powerplay_points = data.get('powerPlayPoints')
        self.powerplay_time_on_ice = data.get('powerPlayTimeOnIce')
        self.even_time_on_ice = data.get('evenTimeOnIce')
        self.penalty_minutes = data.get('penaltyMinutes')
        self.faceoff_percentage = data.get('faceOffPct')
        self.shot_percentage = data.get('shotPct')
        self.game_winning_goals = data.get('gameWinningGoals')
        self.overtime_goals = data.get('overTimeGoals')
        self.shorthanded_goals = data.get('shortHandedGoals')
        self.shorthanded_points = data.get('shortHandedPoints')
        self.shorthanded_time_on_ice = data.get('shortHandedTimeOnIce')
        self.blocked = data.get('blocked')
        self.plus_minus = data.get('plusMinus')
        self.points = data.get('points')
        self.shifts = data.get('shifts')
        self.time_on_ice_per_game = data.get('timeOnIcePerGame')
        self.even_time_on_ice_per_game = data.get('evenTimeOnIcePerGame')
        self.short_handed_time_on_ice_per_game = data.get('shortHandedTimeOnIcePerGame')
        self.power_play_time_on_ice_per_game = data.get('powerPlayTimeOnIcePerGame')


class Team:
    __slots__ = (
        'id',
        'name',
        'link',
        'venue_id',
        'venue_name',
        'venue_link',
        'venue_city',
        'timezone_id',
        'timezone_offset',
        'timezone_tz',
        'abbreviation',
        'team_name',
        'location_name',
        'first_year_of_play',
        'division_id',
        'division_name',
        'division_name_short',
        'division_link',
        'division_abbreviation',
        'conference_id',
        'conference_name',
        'conference_link',
        'franchise_id',
        'franchise_name',
        'franchise_link',
        'short_name',
        'official_website',
        'active'
    )

    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.link = data.get('link')
        self.venue_id = data.get('venue').get('id')
        self.venue_name = data.get('venue').get('name')
        self.venue_link = data.get('venue').get('link')
        self.venue_city = data.get('venue').get('city')
        self.timezone_id = data.get('venue').get('timeZone').get('id')
        self.timezone_offset = data.get('venue').get('timeZone').get('offset')
        self.timezone_tz = data.get('venue').get('timeZone').get('tz')
        self.abbreviation = data.get('abbreviation')
        self.team_name = data.get('teamName')
        self.location_name = data.get('locationName')
        self.first_year_of_play = data.get('firstYearOfPlay')
        self.division_id = data.get('division').get('id')
        self.division_name = data.get('division').get('name')
        self.division_name_short = data.get('division').get('nameShort')
        self.division_link = data.get('division').get('link')
        self.division_abbreviation = data.get('division').get('abbreviation')
        self.conference_id = data.get('conference').get('id')
        self.conference_name = data.get('conference').get('name')
        self.conference_link = data.get('conference').get('link')
        self.franchise_id = data.get('franchise').get('franchiseId')
        self.franchise_name = data.get('franchise').get('teamName')
        self.franchise_link = data.get('franchise').get('link')
        self.short_name = data.get('shortName')
        self.official_website = data.get('officialSiteUrl')
        self.active = data.get('active')


async def get_player(session, player_id):
    url = f"https://statsapi.web.nhl.com/api/v1/people/{player_id}"
    return await fetch(session, url)


async def get_player_single_season(session, player_id):
    url = f"https://statsapi.web.nhl.com/api/v1/people/{player_id}/stats?stats=statsSingleSeason"
    return await fetch(session, url)


async def get_schedule(session, date):
    url = f"https://statsapi.web.nhl.com/api/v1/schedule?date={date}"
    return await fetch(session, url)


async def get_teams(session):
    url = f"https://statsapi.web.nhl.com/api/v1/teams/"
    return await fetch(session, url)


async def get_team_roster(session, team_id):
    url = f"https://statsapi.web.nhl.com/api/v1/teams/{team_id}/roster"
    return await fetch(session, url)


async def get_team_schedule(session, date, team_id):
    url = f"https://statsapi.web.nhl.com/api/v1/schedule?date={date}&teamId={team_id}"
    return await fetch(session, url)


async def search_for_players(name: str):
    players = dict(
        await NHLPlayers
        .select('player_id', 'full_name')
        .gino
        .all()
    )

    match = process.extract(
        name,
        players
    )

    return match


async def search_for_teams(name: str):
    teams = dict(
        await NHLTeams
        .select('team_name', 'team_id')
        .gino
        .all()
    )

    match = process.extract(
        name,
        teams
    )

    return match


async def get_team_id(viking, ctx, name):
    embed = discord.Embed(
        inline=True,
        colour=viking.color,
        title='Team'
    )

    teams = await search_for_teams(name)
    matches = [(name, id) for name, score, id in teams if score > 75]

    if not matches:
        return None

    if len(matches) == 1:
        for name, id in matches:
            return id

    if len(matches) > 1:
        teams = {}

        for index, match in enumerate(matches, 1):
            name, id = match
            teams[id] = f"{index}. {name}"

        options = format_list(
            teams.values(),
            enumerate=True
        )

        embed.add_field(
            inline=False,
            name='Please type a number to select a team:',
            value=options
        )

        await ctx.send(embed=embed)

        def check(message):
            if (message.author == ctx.author and
                    message.channel == ctx.channel):

                try:
                    selection = int(message.content)
                except Exception:
                    pass
                else:
                    if selection >= 1 and selection <= len(matches):
                        return True

        try:
            message = await viking.wait_for(
                'message',
                check=check,
                timeout=15
            )
        except TimeoutError:
            raise
        else:
            team_index = int(message.content) - 1
            _, id = matches[team_index]

            return id

    return matches


async def get_player_id(viking, ctx, name):
    embed = discord.Embed(
        inline=True,
        colour=viking.color,
        title='Profile'
    )

    players = await search_for_players(name)
    matches = [(name, id) for name, score, id in players if score > 75]

    if not matches:
        return None

    if len(matches) == 1:
        for name, id in matches:
            return id

    if len(matches) > 1:
        players = {}

        for index, match in enumerate(matches, 1):
            name, id = match
            players[id] = f"{index}. {name}"

        options = format_list(
            players.values(),
            enumerate=True
        )

        embed.add_field(
            inline=False,
            name='Please type a number to select a player:',
            value=options
        )

        await ctx.send(embed=embed)

        def check(message):
            if (message.author == ctx.author and
                    message.channel == ctx.channel):

                try:
                    selection = int(message.content)
                except Exception:
                    pass
                else:
                    if selection >= 1 and selection <= len(matches):
                        return True

        try:
            message = await viking.wait_for(
                'message',
                check=check,
                timeout=15
            )
        except TimeoutError:
            raise
        else:
            player_index = int(message.content) - 1
            _, id = matches[player_index]

            return id
