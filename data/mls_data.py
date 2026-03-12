from setup.session_setup import session
from datetime import datetime as dt
from datetime import timezone as tz


def get_games(date):
    """ Loads NHL game data for the provided date.

    Args:
        date (date): Date that game data should be pulled for.

    Returns:
        list: List of dicts of game data.
    """
    
    # Create an empty list to hold the game dicts.
    games = []

    # Call the NHL game API for the date specified and store the JSON results.
    #MLS
    url = 'https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/scoreboard?dates='
    games_response = session.get(url=f"{url}{date.strftime(format='%Y%m%d')}")
    games_json = games_response.json()['events']

    # For each game, build a dict recording current game details.
    if games_json: # If games today.
        for game in games_json:
            if game['season']['type'] == 13846 :
                games.append({
                    'league': 'MLS',
                    'game_id': game['id'],
                    'home_abrv': game['competitions'][0]['competitors'][0]['team']['abbreviation'],
                    'away_abrv': game['competitions'][0]['competitors'][1]['team']['abbreviation'],
                    'home_score': game['competitions'][0]['competitors'][0]['score'], # Doesn't exist until game starts.
                    'away_score': game['competitions'][0]['competitors'][1]['score'],
                    'start_datetime_utc': dt.strptime(game['date'], '%Y-%m-%dT%H:%MZ').replace(tzinfo=tz.utc),
                    'start_datetime_local': dt.strptime(game['date'], '%Y-%m-%dT%H:%MZ').replace(tzinfo=tz.utc).astimezone(tz=None), # Convert UTC to local time.
                    'status': game['competitions'][0]['status']['type']['state'],
                    'has_started': True if game['competitions'][0]['status']['type']['state'] in ['in'] else False,
                    'period_num': game['competitions'][0]['status']['period'] if 'period' in game['competitions'][0]['status'] else "NULL", # Doesn't until game starts.
                    'period_time_remaining': game['competitions'][0]['status']['displayClock'], # clock doesn't exist until game starts.
                    'is_intermission': True if game['competitions'][0]['status']['type']['name'] == "STATUS_HALFTIME" else False,
                    # Will set the remaining later, default to False and None for now.
                    'home_team_scored': False,
                    'away_team_scored': False,
                    'scoring_team': None
                })

    return games


def get_next_game(team):
    """ Loads next game details for the supplied NHL team.
    If the team is currently playing, will return details of the current game.

    Args:
        5team (str): Three char abbreviation of the team to pull next game details for.

    Returns:
            dict: Dict of next game details.
    """
    
    # Note the current datetime.
    cur_datetime = dt.today().astimezone()
    cur_date = dt.today().astimezone().date()

    #Get Team ID
    url = 'https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/teams'
    teams_response = session.get(url=url)
    teams_json = teams_response.json()['sports'][0]['leagues'][0]['teams']

    for league_team in teams_json:
        if league_team['team']['abbreviation'] == team:
            team_id = league_team['team']['id']
    
    # Call the NHL schedule API for the team specified and store the JSON results.
    url = f'https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/teams/{team_id}'
    next_game_response = session.get(url=url)
    next_game_json = next_game_response.json()['team']['nextEvent']
    next_game_details = next_game_json

    if next_game_details:
        for game in next_game_details:
            # Put together a dictionary with needed details.
            next_game = {
                'home_or_away': 'away' if game['competitions'][0]['competitors'][0]['team']['abbreviation'] != team else 'home',
                'opponent_abrv': game['competitions'][0]['competitors'][0]['team']['abbreviation'] if game['competitions'][0]['competitors'][0]['team']['abbreviation'] != team else game['competitions'][0]['competitors'][1]['team']['abbreviation'],
                'start_datetime_utc': dt.strptime(game['date'], '%Y-%m-%dT%H:%MZ').replace(tzinfo=tz.utc),
                'start_datetime_local': dt.strptime(game['date'], '%Y-%m-%dT%H:%MZ').replace(tzinfo=tz.utc).astimezone(tz=None),
                'is_today': True if dt.strptime(game['date'], '%Y-%m-%dT%H:%MZ').replace(tzinfo=tz.utc).astimezone(tz=None).date() == cur_date or dt.strptime(game['date'], '%Y-%m-%dT%H:%MZ').replace(tzinfo=tz.utc).astimezone(tz=None) < cur_datetime else False, # TODO: clean this up. Needed in case game is still going when date rolls over.
                #'has_started': True if game['gameState'] in ('LIVE', 'CRIT') else False
            }
            return(next_game)
    
    # If no next game found, return None.
    return None
