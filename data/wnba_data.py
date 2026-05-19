from setup.session_setup import session
from datetime import datetime as dt
from datetime import timezone as tz

# Note API headers that will need to be used for stats and cdn endpoints.
stats_headers = {
    'host': 'stats.nba.com',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.5',
    'accept-encoding': 'gzip, deflate, br',
    'connection': 'keep-alive',
    'referer': 'https://www.nba.com/',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    'sec-ch-ua-mobile': '?0',
    'sec-fetch-dest': 'empty'
}

cdn_headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'connection': 'keep-alive',
    'host': 'cdn.nba.com',
    'referer': 'https://www.nba.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
}

def get_games(date):
    """ Loads WNBA game data for the provided date.

    Args:
        date (date): Date that game data should be pulled for.

    Returns:
        list: List of dicts of game data.
    """

    # Create an empty list to hold the game dicts.
    games = []

    # First, hit the todayScoreboard endpoint to see what date it is returning.
    url = 'https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_10.json'
    games_response = session.get(url=url, headers=cdn_headers)
    games_response_date = dt.strptime(games_response.json()['scoreboard']['gameDate'], '%Y-%m-%d').date()

    # If the date returned by the live score endpoint matches the date requested, use these results.
    if games_response_date == date:
        games_json = games_response.json()['scoreboard']['games']

    # Otherwise, hit the scoreboardv3 endpoint w/ the date param.
    else:
        # Call the WNBA game API for the date specified and store the JSON results.
        url = 'https://stats.nba.com/stats/scoreboardv3?LeagueID=10'    
        games_response = session.get(url=f"{url}&GameDate={date.strftime(format='%Y-%m-%d')}", headers=stats_headers)
        games_json = games_response.json()['scoreboard']['games']

    # For each game, build a dict recording current game details.
    if games_json: # If games today.
        for game in games_json:
            if 'All-Star' not in game['gameLabel'] and 'Preseason' not in game['gameLabel']: # This should leave regular season and playoff games.
                games.append({
                    'game_id': game['gameId'],
                    'home_abrv': game['homeTeam']['teamTricode'],
                    'away_abrv': game['awayTeam']['teamTricode'],
                    'home_score': game['homeTeam']['score'],
                    'away_score': game['awayTeam']['score'],
                    'start_datetime_utc': dt.strptime(game['gameTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc),
                    'start_datetime_local': dt.strptime(game['gameTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None), # Convert UTC to local time.
                    'status': game['gameStatusText'],
                    'status_code': game['gameStatus'], # 1=Scheduled, 2=In Progress, 3=Final.
                    'has_started': True if game['gameStatus'] > 1 else False,
                    'period_num': game['period'],
                    'period_type': 'OT' if game['period'] > 4 else 'Std',
                    'period_time_remaining': game['gameClock'][2:4] + ':' + game['gameClock'][5:7] if game['gameClock'] != ':' else None, # API returns time remaining in PT##M##.##S format.
                    'is_halftime': True if game['gameClock'] == 'PT00M00.00S' and game['period'] == 2 else False, # No explicit halftime flag, so infer based on period and clock.
                    # Will set the remaining later, default to False and None for now.
                    'home_team_scored': False,
                    'away_team_scored': False,
                    'scoring_team': None
                })

    # Sort games by game_id, ensuring that order remains consistent after games start/end.
    games = sorted(games, key=lambda x: x['game_id'])

    return games


def get_next_game(team):
    """ Loads next game details for the supplied WNBA team.
    If the team is currently playing, will return details of the current game.

    Args:
        team (str): Three char abbreviation of the team to pull next game details for.

    Returns:
            dict: Dict of next game details.
    """

    # Get the current WNBA season based on the current date.
    season = determine_current_season()

    # Call the WNBA schedule API for the team specified and store the JSON results.
    # TODO: Save these results to avoid multiple calls if multiple favorite teams are set.
    url = 'https://stats.nba.com/stats/scheduleleaguev2?LeagueID=10'   
    schedule_response = session.get(url=f'{url}&Season={season}', headers=stats_headers)
    schedule_json = schedule_response.json()['leagueSchedule']['gameDates']

    # Determine the future games.
    cur_datetime = dt.today().astimezone()
    cur_date = cur_datetime.date()
    upcoming_days_games = [day_games for day_games in schedule_json if dt.strptime(day_games['gameDate'], '%m/%d/%Y %H:%M:%S').date() >= cur_date]
    
    # Determine the next game for the team specified and return game details.
    for day_game in upcoming_days_games:
        for game in day_game['games']:
            if game['gameLabel'] != 'Preseason': # This should leave regular season and playoff games.
                if game['homeTeam']['teamTricode'] == team or game['awayTeam']['teamTricode'] == team:
                    # Put together a dictionary with needed details.
                    next_game = {
                        'home_or_away': 'away' if game['homeTeam']['teamTricode'] != team else 'home',
                        'opponent_abrv': game['homeTeam']['teamTricode'] if game['homeTeam']['teamTricode'] != team else game['awayTeam']['teamTricode'],
                        'start_datetime_utc': dt.strptime(game['gameDateTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc),
                        'start_datetime_local': dt.strptime(game['gameDateTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None),
                        'is_today': True if dt.strptime(game['gameDateTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None).date() == cur_date or dt.strptime(game['gameDateTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None) < cur_datetime else False, # TODO: clean this up. Needed in case game is still going when date rolls over.
                        'has_started': True if cur_datetime >= dt.strptime(game['gameDateTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None) else False
                    }

                    # Skip to next game if this one has started more than 3 hours ago (longer than an avg game). Schedule API doesn't update in real-time w/ game status.
                    if next_game['has_started'] and (cur_datetime - next_game['start_datetime_local']).total_seconds() > 10800:
                        continue

                    return(next_game)
    
    # If no next game found, return None.
    return None


def get_standings():
    """ Loads current WNBA standings by division, conference, and overall league.

    Returns:
        dict: Dict containing all standings by each category.
    """

    # Get the current WNBA season based on the current date.
    season = determine_current_season()

    # Call the WNBA standings API and store the JSON results.
    url = 'https://stats.nba.com/stats/leaguestandingsv3?LeagueID=10&SeasonType=Regular Season'
    standings_response = session.get(url=f'{url}&Season={season}', headers=stats_headers)
    standings_json_unprocessed = standings_response.json()['resultSets'][0]

    # Process the returned JSON into a more usable format.
    standings_json = []
    for team in standings_json_unprocessed['rowSet']:
        team_values = {}
        for header, value in zip(standings_json_unprocessed['headers'], team):
            team_values[header] = value
        
        # Add the team abbreviation to the dict based on the dict defined above.
        team_values['teamTricode'] = determine_team_abbreviation(team_values['TeamID'])
        standings_json.append(team_values)

    # Set up structure of the returned dict.
    # Teams lists will be populated w/ the API results.
    standings = {
        'retrieved_on': dt.now().astimezone(),
        'league': {
            'WNBA': { # Match structure needed for other standing types.
                'rank_method': 'Win Percentage',
                'playoff_cutoff_hard': 8,
                'team_standings': [] # Will be populated w/ the API results.
            }
        }
    }

    # Populate the team lists w/ dicts containing details of each team.
    # API returns teams in overall standing order, so generally won't have to sort.
    for team in standings_json:
        # Overall.
        standings['league']['WNBA']['team_standings'].append({
                'team_abrv': team['teamTricode'],
                'rank': team['PlayoffRank'],
                'percent': f'{team["WinPCT"]:.3f}', # Make percent a string formatted to 3 decimal places. E.g., 0.625.
                'has_clinched': True if team['ClinchIndicator'] == ' - x' else False # ClinchedPostSeason isn't populated in WNBA API.
        })

    return standings


def determine_current_season():
    """ Determines the current WNBA season based on the current date.

    Returns:
        str: Current WNBA season in 'YYYY' format.
    """

    cur_date = dt.today().astimezone().date()
    season = str(cur_date.year)
    return season


def determine_team_abbreviation(team_id):
    """ Gets team abbreviation (tricode) based on team ID.

    Args:
        team_id (int): ID of the WNBA team per the WNBA API.

    Returns:
        str: Team tricode.
    """

    # Mapping of WNBA teams IDs to abbreviations. Needed since schedule API does not return abbreviations.
    team_ids_to_abbreviations = {
        1611661313: 'NYL',
        1611661317: 'PHO',
        1611661319: 'LVA',
        1611661320: 'LAS',
        1611661321: 'DAL',
        1611661322: 'WAS',
        1611661323: 'CON',
        1611661324: 'MIN',
        1611661325: 'IND',
        1611661327: 'POR',
        1611661328: 'SEA',
        1611661329: 'CHI',
        1611661330: 'ATL',
        1611661331: 'GSV',
        1611661332: 'TOR'
    }

    return team_ids_to_abbreviations.get(team_id, None)