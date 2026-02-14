from setup.session_setup import session
from datetime import datetime as dt
from datetime import timezone as tz


def get_games(date):
    """ Loads NBA game data for the provided date.

    Args:
        date (date): Date that game data should be pulled for.

    Returns:
        list: List of dicts of game data.
    """

    # Create an empty list to hold the game dicts.
    games = []

    # First, hit the todayScoreboard endpoint to see what date it is returning.
    url = 'https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json'
    games_response = session.get(url=url)
    games_response_date = dt.strptime(games_response.json()['scoreboard']['gameDate'], '%Y-%m-%d').date()

    # If the date returned by the live score endpoint matches the date requested, use these results.
    if games_response_date == date:
        games_json = games_response.json()['scoreboard']['games']

    # Otherwise, hit the scoreboardv3 endpoint w/ the date param.
    else:
        # Call the NBA game API for the date specified and store the JSON results.
        url = 'https://stats.nba.com/stats/scoreboardv3?LeagueID=00'    
        headers = {
            'host': "stats.nba.com",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            'accept': "application/json, text/plain, */*",
            'accept-language': "en-US,en;q=0.5",
            'accept-encoding': "gzip, deflate, br",
            'connection': "keep-alive",
            'referer': "https://stats.nba.com/",
            'pragma': "no-cache",
            'cache-control': "no-cache",
            'sec-ch-ua': "\"Chromium\";v=\"140\", \"Google Chrome\";v=\"140\", \"Not;A=Brand\";v=\"24\"",
            'sec-ch-ua-mobile': "?0",
            'sec-fetch-dest': "empty"
        }
        games_response = session.get(url=f"{url}&GameDate={date.strftime(format='%Y-%m-%d')}", headers=headers)
        games_json = games_response.json()['scoreboard']['games']

    # For each game, build a dict recording current game details.
    if games_json: # If games today.
        for game in games_json:
            if 'All-Star' not in game['gameLabel'] and 'Preseason' not in game['gameLabel'] and 'Rising Stars' not in game['gameLabel']: # This should leave regular season and playoff games.
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
    """ Loads next game details for the supplied NBA team.
    If the team is currently playing, will return details of the current game.

    Args:
        team (str): Three char abbreviation of the team to pull next game details for.

    Returns:
            dict: Dict of next game details.
    """

    # Get the current NBA season based on the current date.
    season = determine_current_season()

    # Call the NBA schedule API for the team specified and store the JSON results.
    # TODO: Save these results to avoid multiple calls if multiple favorite teams are set.
    url = 'https://stats.nba.com/stats/scheduleleaguev2?LeagueID=00'   
    headers = {
        'host': "stats.nba.com",
        'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        'accept': "application/json, text/plain, */*",
        'accept-language': "en-US,en;q=0.5",
        'accept-encoding': "gzip, deflate, br",
        'connection': "keep-alive",
        'referer': "https://stats.nba.com/",
        'pragma': "no-cache",
        'cache-control': "no-cache",
        'sec-ch-ua': "\"Chromium\";v=\"140\", \"Google Chrome\";v=\"140\", \"Not;A=Brand\";v=\"24\"",
        'sec-ch-ua-mobile': "?0",
        'sec-fetch-dest': "empty"
    }
    schedule_response = session.get(url=f'{url}&Season={season}', headers=headers)
    schedule_json = schedule_response.json()['leagueSchedule']['gameDates']

    # Determine the future games.
    cur_datetime = dt.today().astimezone()
    cur_date = cur_datetime.date()
    upcoming_days_games = [day_games for day_games in schedule_json if dt.strptime(day_games['gameDate'], '%m/%d/%Y %H:%M:%S').date() >= cur_date]
    
    # Determine the next game for the team specified and return game details.
    for day_game in upcoming_days_games:
        for game in day_game['games']:
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
    """ Loads current NBA standings by division, conference, and overall league.

    Returns:
        dict: Dict containing all standings by each category.
    """

    # Get the current NBA season based on the current date.
    season = determine_current_season()

    # Call the NBA standings API and store the JSON results.
    url = 'https://stats.nba.com/stats/leaguestandingsv3?LeagueID=00&SeasonType=Regular Season'    
    headers = {
        'host': "stats.nba.com",
        'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        'accept': "application/json, text/plain, */*",
        'accept-language': "en-US,en;q=0.5",
        'accept-encoding': "gzip, deflate, br",
        'connection': "keep-alive",
        'referer': "https://stats.nba.com/",
        'pragma': "no-cache",
        'cache-control': "no-cache",
        'sec-ch-ua': "\"Chromium\";v=\"140\", \"Google Chrome\";v=\"140\", \"Not;A=Brand\";v=\"24\"",
        'sec-ch-ua-mobile': "?0",
        'sec-fetch-dest': "empty"
    }
    standings_response = session.get(url=f'{url}&Season={season}', headers=headers)
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
        'rank_method': 'Win Percentage',
        'division': {
            'divisions': {
                'Atlantic': {
                    'abrv': 'Atl',
                    'teams': []
                },
                'Central': {
                    'abrv': 'Cen',
                    'teams': []
                },
                'Southeast': {
                    'abrv': 'SE',
                    'teams': []
                },
                'Northwest': {
                    'abrv': 'NW',
                    'teams': []
                },
                'Pacific': {
                    'abrv': 'Pac',
                    'teams': []
                },
                'Southwest': {
                    'abrv': 'SW',
                    'teams': []
                }
            }
        },

        'conference': {
            'playoff_cutoff_hard': 10,
            'playoff_cutoff_soft': 6,
            'conferences': {
                'East': {
                    'abrv': 'Est',
                    'teams': []
                },
                'West': {
                    'abrv': 'Wst',
                    'teams': []
                },
            }
        }
    }

    # Populate the team lists w/ dicts containing details of each team.
    # API returns teams in overall standing order, so generally won't have to sort.
    for team in standings_json:
        # Divisions.
        standings['division']['divisions'][team['Division']]['teams'].append(
            {
                'team_abrv': team['teamTricode'],
                'rank': team['DivisionRank'],
                'percent': f'{team["WinPCT"]:.3f}', # Make percent a string formatted to 3 decimal places. E.g., 0.625.
                'has_clinched': True if team['ClinchedPostSeason'] == 1 else False
            }
        )

        # Conference.
        standings['conference']['conferences'][team['Conference']]['teams'].append(
            {
                'team_abrv': team['teamTricode'],
                'rank': team['PlayoffRank'],
                'percent': f'{team["WinPCT"]:.3f}', # Make percent a string formatted to 3 decimal places. E.g., 0.625.
                'has_clinched': True if team['ClinchedPostSeason'] == 1 else False
            }
        )

    return standings


def determine_current_season():
    """ Determines the current NBA season based on the current date.

    Returns:
        str: Current NBA season in 'YYYY-YY' format.
    """

    cur_date = dt.today().astimezone().date()
    season = f'{cur_date.year}-{str(cur_date.year + 1)[2:4]}' if cur_date.month >= 7 else f'{cur_date.year -1}-{str(cur_date.year)[2:4]}'
    return season


def determine_team_abbreviation(team_id):
    """ Gets team abbreviation (tricode) based on team ID.

    Args:
        team_id (int): ID of the NBA team per the NBA API.

    Returns:
        str: Team tricode.
    """

    # Mapping of NBA teams IDs to abbreviations. Needed since schedule API does not return abbreviations.
    team_ids_to_abbreviations = {
        1610612737: 'ATL',
        1610612738: 'BOS',
        1610612739: 'CLE',
        1610612740: 'NOP',
        1610612741: 'CHI',
        1610612742: 'DAL',
        1610612743: 'DEN',
        1610612744: 'GSW',
        1610612745: 'HOU',
        1610612746: 'LAC',
        1610612747: 'LAL',
        1610612748: 'MIA',
        1610612749: 'MIL',
        1610612750: 'MIN',
        1610612751: 'BKN',
        1610612752: 'NYK',
        1610612753: 'ORL',
        1610612754: 'IND',
        1610612755: 'PHI',
        1610612756: 'PHX',
        1610612757: 'POR',
        1610612758: 'SAC',
        1610612759: 'SAS',
        1610612760: 'OKC',
        1610612761: 'TOR',
        1610612762: 'UTA',
        1610612763: 'MEM',
        1610612764: 'WAS',
        1610612765: 'DET',
        1610612766: 'CHA'
    }

    return team_ids_to_abbreviations.get(team_id, None)