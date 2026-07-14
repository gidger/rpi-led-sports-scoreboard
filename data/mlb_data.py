from setup.session_setup import session
from datetime import datetime as dt
from datetime import timezone as tz


def get_games(date):
    """ Loads MLB game data for the provided date.

    Args:
        date (date): Date that game data should be pulled for.

    Returns:
        list: List of dicts of game data.
    """
    
    # Create an empty list to hold the game dicts.
    games = []

    # Build the URL for the MLB games scehdule API call.
    base_url = 'https://statsapi.mlb.com/api/v1/schedule/games/'
    url_params = {
        'sportId': 1,  # MLB sport ID
        'date': date.strftime('%Y-%m-%d'), # Format date as YYYY-MM-DD 
        'hydrate': [ # Hydrations add extra details to the API response.
            'team',
            'linescore'
        ],
        'fields': [ # Fields filter to limit API response to only the data we need.
            'totalGames',
            'dates',
            'games',
            'gamePk',
            'gameType',
            'gameDate',
            'status',
            'abstractGameState',
            'detailedState',
            'startTimeTBD',
            'linescore',
            'teams',
            'away',
            'team',
            'abbreviation',
            'home',
            'team',
            'abbreviation',
            'linescore',
            'currentInning',
            'inningState',
            'teams',
            'home',
            'runs',
            'away',
            'runs',
            'outs',
            'offense',
            'first',
            'second',
            'third'
        ]
    }
    url = base_url + '?' + '&'.join([f'{key}={",".join(value) if isinstance(value, list) else value}' for key, value in url_params.items()])
    
    # Call the MLB game API for the date specified and store the JSON results.
    games_response = session.get(url=url)
    games_json = games_response.json()['dates'][0]['games']

    # For each game, build a dict recording current game details.
    if games_json: # If games today.
        for game in games_json:
            if game['gameType'] != 'A': # Ignore the all-star game..
                games.append({
                    'game_id': game['gamePk'],
                    'home_abrv': game['teams']['home']['team']['abbreviation'],
                    'away_abrv': game['teams']['away']['team']['abbreviation'],
                    'home_score': game.get('linescore', {}).get('teams', {}).get('home', {}).get('runs', 0), # These won't exist until the game starts.
                    'away_score': game.get('linescore', {}).get('teams', {}).get('away', {}).get('runs', 0),
                    'start_datetime_utc': dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc),
                    'start_datetime_local': dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None), # Convert UTC to local time.
                    'start_time_tbd': game['status']['startTimeTBD'],
                    'status': game['status']['abstractGameState'],
                    'detailed_status': game['status']['detailedState'],
                    'has_started': True if game['status']['abstractGameState'] in ['Live', 'Final'] else False,
                    'inning_num': game.get('linescore', {}).get('currentInning'), # These won't exist until the game starts.
                    'inning_state': game.get('linescore', {}).get('inningState'),
                    'outs': game.get('linescore', {}).get('outs', 0),
                    'runner_on_first': True if 'first' in game.get('linescore', {}).get('offense', {}) else False,
                    'runner_on_second': True if 'second' in game.get('linescore', {}).get('offense', {}) else False,
                    'runner_on_third': True if 'third' in game.get('linescore', {}).get('offense', {}) else False,
                    'home_team_scored': False, # These will be populated later based on score changes, but default to False for now.
                    'away_team_scored': False,
                    'scoring_team': None
                })

    # Sort games by start datetime and game ID to ensure consistent order. Start datetime needed since game IDs can have a weird order due to postponement, etc.
    games = sorted(games, key=lambda x: (x['start_datetime_utc'], x['game_id']))
            
    return games


def get_next_game(team):
    """ Loads next game details for the supplied MLB team.
    If the team is currently playing, will return details of the current game.

    Args:
        team (str): Team abbreviation to pull next game details for.

    Returns:
        dict: Dict of next game details.
    """

    # Note current datetime.
    cur_datetime = dt.today().astimezone()
    cur_date = cur_datetime.date()

    # Convert provided team abbreviation to team ID for the API call.
    team_id = determine_team_abbreviation(team)

    # Build the URL for the MLB teams API call.
    base_url = 'https://statsapi.mlb.com/api/v1/teams/'
    url_params = {
        'teamId': team_id,
        'hydrate': [ # Hydrations add extra details to the API response.
            'nextSchedule(team)',
        ],
        'fields': [ # Fields filter to limit API response to only the data we need.
            'teams',
            'nextGameSchedule',
            'dates',
            'games',
            'gameDate',
            'status',
            'abstractGameState',
            'detailedState',
            'teams',
            'away',
            'team',
            'abbreviation'
        ]
    }
    url = base_url + '?' + '&'.join([f'{key}={",".join(value) if isinstance(value, list) else value}' for key, value in url_params.items()])
    
    # Call the MLB team API for the team specified (hydrated with next games details) and store the JSON results.
    games_response = session.get(url=url)
    all_schedule_json = games_response.json()['teams'][0]['nextGameSchedule']['dates']

    # Since an MLB team can play multiple games in a day, we'll need to flatten.
    schedule_json = []
    for game_date in all_schedule_json:
        for game in game_date['games']:
            schedule_json.append(game)

    # Determine the next game for the team specified and return game details.
    for game in schedule_json:
        if game['status']['abstractGameState'] in ['Preview', 'Live']:
            # Put together a dictionary with needed details.
            next_game = {
                'home_or_away': 'away' if game['teams']['home']['team']['abbreviation'] != team else 'home',
                'opponent_abrv': game['teams']['home']['team']['abbreviation'] if game['teams']['home']['team']['abbreviation'] != team else game['teams']['away']['team']['abbreviation'],
                'start_datetime_utc': dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc),
                'start_datetime_local': dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None),
                'is_today': True if dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None).date() == cur_date or dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None) < cur_datetime else False, # TODO: clean this up. Needed in case game is still going when date rolls over.
                'has_started': True if cur_datetime >= dt.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None) else False
            }
            return(next_game)
    
    # If no next game found, return None.
    return None


def get_standings():
    """ Loads current MLB standings by league wildcard.

    Returns:
        dict: Dict containing all standings by each category.
    """

    # Build the URL for the MLB standings API call.
    base_url = 'https://statsapi.mlb.com/api/v1/standings/'
    url_params = {
        'standingsType': 'regularSeason',
        'season': dt.today().year,
        'leagueId': [
            '103', # AL
            '104'  # NL
        ],
        'hydrate': [ # Hydrations add extra details to the API response.
            'team',
        ],
        'fields': [ # Fields filter to limit API response to only the data we need.
            'records',
            'teamRecords',
            'team',
            'abbreviation',
            'league',
            'name',
            'division',
            'name',
            'leagueRank',
            'divisionRank',
            'wildCardRank',
            'wildCardGamesBack',
            'clinched',
            'winningPercentage'
        ]
    }
    url = base_url + '?' + '&'.join([f'{key}={",".join(value) if isinstance(value, list) else value}' for key, value in url_params.items()])
    
    # Call the MLB team API for standings (hydrated with team details) and store the JSON results.
    standings_response = session.get(url=url)
    all_standings_json = standings_response.json()['records']

    # Flatten into a single list of teams since the API returns teams grouped by division and we want to sort by wildcard rank across the league.
    standings_json = []
    for div in all_standings_json:
        for team in div['teamRecords']:
            standings_json.append(team)

    # Set up structure of the returned dict.
    # Teams lists will be populated w/ the API results.
    standings = {
        'retrieved_on': dt.now().astimezone(),
        'league': {
            league: {
                'subdivision_abrv': league_abrv,
                'rank_method': 'Win Percentage',
                'team_standings': [] # Will be populated w/ the API results.
            } for league, league_abrv in [('American League', 'AL'), ('National League', 'NL')]
        },
        'wildcard': {
            league: {
                'subdivision_abrv': league_abrv,
                'rank_method': 'Win Percentage',
                'playoff_cutoff_hard': 6,
                'playoff_cutoff_soft': 2,
                'team_standings': [] # Will be populated w/ the API results.
            } for league, league_abrv in [('American League', 'AL'), ('National League', 'NL')]
        },
        'division': {
            div: {
                'subdivision_abrv': div_abrv,
                'rank_method': 'Win Percentage',
                'playoff_cutoff_soft': 1,
                'team_standings': [] # Will be populated w/ the API results.
            } for div, div_abrv in [
                ('American League East', 'ALE'),
                ('American League Central', 'ALC'),
                ('American League West', 'ALW'),
                ('National League East', 'NLE'),
                ('National League Central', 'NLC'),
                ('National League West', 'NLW')
            ]
        }
    }

    # Populate the team lists w/ dicts containing details of each team.
    # API returns teams in overall standing order, so generally won't have to sort.
    for team in standings_json:
        # League (NL/AL).
        standings['league'][team['team']['league']['name']]['team_standings'].append({
            'team_abrv': team['team']['abbreviation'],
            'rank': team['leagueRank'],
            'percent': '0' + team['winningPercentage'] if team['winningPercentage'] != '1.000' else team['winningPercentage'], # Reformating to match winning percentage format used in standings images.
            'has_clinched': team['clinched']
        })

        # Wildcards by league.
        standings['wildcard'][team['team']['league']['name']]['team_standings'].append({
            'team_abrv': team['team']['abbreviation'],
            'rank': team.get('wildCardRank', str(team['team']['division']['name'].split()[-1][0]) + team['divisionRank']), # Top teams in each division won't have a wildCardRank, so we'll use their division rank instead.
            
            # Rank helper will allow us to group top 3 div leaders so they appear together at the top of the WC standings.
            'rank_helper': 1 if team['divisionRank'] == '1' else int(team.get('wildCardRank')) + 1, # +1 to force WC teams to be ranked below division leaders. This is a bit hacky, but works.
            'rank_helper_tiebreaker': int(team['leagueRank']), # In cases where teams have the same wildCardRank (div leaders), we'll use league rank as a tie breaker to ensure correct ordering.
            'percent': '0' + team['winningPercentage'] if team['winningPercentage'] != '1.000' else team['winningPercentage'], # Reformating to match winning percentage format used in standings images.
            'has_clinched': team['clinched']
        })

        # Division.
        standings['division'][team['team']['division']['name']]['team_standings'].append({
            'team_abrv': team['team']['abbreviation'],
            'rank': team['divisionRank'],
            'percent': '0' + team['winningPercentage'] if team['winningPercentage'] != '1.000' else team['winningPercentage'], # Reformating to match winning percentage format used in standings images.
            'has_clinched': team['clinched']
        })

    # Sort league team standings by rank within each league.
    for league in standings['league'].values():
        league['team_standings'] = sorted(league['team_standings'], key=lambda d: int(d['rank']))

    # Sort WC league team standings by rank_helper and rank_helper_tiebreaker within each league.
    for league in standings['wildcard'].values():
        league['team_standings'] = sorted(league['team_standings'], key=lambda d: (d['rank_helper'], d['rank_helper_tiebreaker']))

    # Sort division team standings by rank within each division.
    for division in standings['division'].values():
        division['team_standings'] = sorted(division['team_standings'], key=lambda d: int(d['rank']))

    return standings


def determine_team_abbreviation(team_abrv):
    """ Gets team ID (int) based on team abbreviation.

    Args:
        team_abrv (str): Abbreviation of the MLB team.

    Returns:
        int: Team ID.
    """

    # Mapping of MLB teams abbreviations to IDs. Needed since schedule API only accepts ID as input.
    team_abbreviations_to_ids = {
        'ATH': 133,
        'PIT': 134,
        'SD':  135,
        'SEA': 136,
        'SF':  137,
        'STL': 138,
        'TB':  139,
        'TEX': 140,
        'TOR': 141,
        'MIN': 142,
        'PHI': 143,
        'ATL': 144,
        'CWS': 145,
        'MIA': 146,
        'NYY': 147,
        'MIL': 158,
        'LAA': 108,
        'AZ':  109,
        'BAL': 110,
        'BOS': 111,
        'CHC': 112,
        'CIN': 113,
        'CLE': 114,
        'COL': 115,
        'DET': 116,
        'HOU': 117,
        'KC':  118,
        'LAD': 119,
        'WSH': 120,
        'NYM': 121
    }

    return team_abbreviations_to_ids.get(team_abrv, None)