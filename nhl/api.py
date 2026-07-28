from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from rapidfuzz import process
from slapshot import Team

if TYPE_CHECKING:
    from slapshot import AsyncNHL, PlayerLanding


TEAM_NAMES = {
    'Anaheim Ducks': Team.ANAHEIM,
    'Boston Bruins': Team.BOSTON,
    'Buffalo Sabres': Team.BUFFALO,
    'Calgary Flames': Team.CALGARY,
    'Carolina Hurricanes': Team.CAROLINA,
    'Chicago Blackhawks': Team.CHICAGO,
    'Colorado Avalanche': Team.COLORADO,
    'Columbus Blue Jackets': Team.COLUMBUS,
    'Dallas Stars': Team.DALLAS,
    'Detroit Red Wings': Team.DETROIT,
    'Edmonton Oilers': Team.EDMONTON,
    'Florida Panthers': Team.FLORIDA,
    'Los Angeles Kings': Team.LOS_ANGELES,
    'Minnesota Wild': Team.MINNESOTA,
    'Montreal Canadiens': Team.MONTREAL,
    'Nashville Predators': Team.NASHVILLE,
    'New Jersey Devils': Team.NEW_JERSEY,
    'New York Islanders': Team.NY_ISLANDERS,
    'New York Rangers': Team.NY_RANGERS,
    'Ottawa Senators': Team.OTTAWA,
    'Philadelphia Flyers': Team.PHILADELPHIA,
    'Pittsburgh Penguins': Team.PITTSBURGH,
    'San Jose Sharks': Team.SAN_JOSE,
    'Seattle Kraken': Team.SEATTLE,
    'St. Louis Blues': Team.ST_LOUIS,
    'Tampa Bay Lightning': Team.TAMPA_BAY,
    'Toronto Maple Leafs': Team.TORONTO,
    'Utah Mammoth': Team.UTAH,
    'Vancouver Canucks': Team.VANCOUVER,
    'Vegas Golden Knights': Team.VEGAS,
    'Washington Capitals': Team.WASHINGTON,
    'Winnipeg Jets': Team.WINNIPEG,
}


async def player_get(client: AsyncNHL, player_name: str) -> PlayerLanding | None:
    results = await client.players.search(player_name, limit=1, active=True)

    if not results:
        results = await client.players.search(player_name, limit=1)

    if not results:
        return None

    player_identifier = int(results[0].player_id)
    return await client.players.landing(player_identifier)


def team_get(team_name: str) -> Team:
    abbreviation = team_name.strip().upper()

    for team in Team:
        if team.value == abbreviation:
            return team

    match, _, _ = process.extractOne(
        team_name,
        TEAM_NAMES.keys()
    )

    return TEAM_NAMES[match]
