from setup.session_setup import session
from datetime import datetime as dt
from datetime import timezone as tz
from datetime import timedelta as td
from pathlib import Path

def get_games(date, self):
    """ Loads league game data for the provided date.

    Args:
        date (date): Date that game data should be pulled for.

    Returns:
        list: List of dicts of game data.
    """
    
    # Create an empty list to hold the game dicts.
    games = []

    # Call the ESPN API for the date specified and store the JSON results.

    url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/{self.LEAGUE.split('-')[-1].lower()}-college-basketball/scoreboard?dates='
    games_response = session.get(url=f"{url}{date.strftime(format='%Y%m%d')}")
    games_json = games_response.json()['events']

    # For each game, build a dict recording current game details.
    if games_json: # If games today.
        for game in games_json:
            #If Regular or postseason
            if game['season']['type'] in [2, 3] :
                games.append({
                    'game_id': game['id'],
                    'home_abrv': game['competitions'][0]['competitors'][0]['team']['abbreviation'],
                    'home_rank': game['competitions'][0]['competitors'][0]['curatedRank']['current'],
                    'away_abrv': game['competitions'][0]['competitors'][1]['team']['abbreviation'],
                    'away_rank': game['competitions'][0]['competitors'][1]['curatedRank']['current'],
                    'home_score': game['competitions'][0]['competitors'][0]['score'], # Doesn't exist until game starts.
                    'away_score': game['competitions'][0]['competitors'][1]['score'],
                    'start_datetime_utc': dt.strptime(game['date'], '%Y-%m-%dT%H:%MZ').replace(tzinfo=tz.utc),
                    'start_datetime_local': dt.strptime(game['date'], '%Y-%m-%dT%H:%MZ').replace(tzinfo=tz.utc).astimezone(tz=None), # Convert UTC to local time.
                    'status': game['competitions'][0]['status']['type']['state'],
                    'has_started': True if game['competitions'][0]['status']['type']['state'] in ['in'] else False,
                    'period_num': game['competitions'][0]['status']['period'] if 'period' in game['competitions'][0]['status'] else "NULL", # Doesn't until game starts.
                    'period_type': 'OT' if game['competitions'][0]['status']['period'] > 2 else 'Std',
                    'period_time_remaining': game['competitions'][0]['status']['displayClock'], # clock doesn't exist until game starts.
                    'is_intermission': True if game['competitions'][0]['status']['type']['name'] in ["STATUS_HALFTIME", 'STATUS_END_PERIOD'] else False,
                    # Will set the remaining later, default to False and None for now.
                    'home_team_scored': False,
                    'away_team_scored': False,
                    'scoring_team': None
                })

    return games


def get_next_game(team, self):
    """ Loads next game details for the supplied team.
    If the team is currently playing, will return details of the current game.

    Args:
        5team (str): Three char abbreviation of the team to pull next game details for.

    Returns:
            dict: Dict of next game details.
    """
    
    # Note the current datetime.
    cur_datetime = dt.today().astimezone()
    cur_date = dt.today().astimezone().date()
    
    team_id = get_team_id(team, self)

    # Call the ESPN schedule API for the team specified and store the JSON results.
    url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/{self.LEAGUE.split('-')[-1].lower()}-college-basketball/teams/{team_id}'
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
                'has_started': True if game['competitions'][0]['status']['type']['state'] in ['in', 'post'] else False
            }
            return(next_game)
    
    # If no next game found, return None.
    return None

def get_team_id(team, self):
    url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/{self.LEAGUE.split('-')[-1].lower()}-college-basketball/scoreboard?dates='
    teams_response = session.get(url=f"{url}{(dt.now()).strftime(format='%Y%m%d')}")
    teams_json = teams_response.json()['events']
    for game in teams_json:
        for teams in game['competitions'][0]['competitors'] :
            if teams['team']['abbreviation'] == team:
                team_id = teams['team']['id']
    
    if 'team_id' in locals():
        return team_id
    else:
        teams_response = session.get(url=f"{url}{(dt.now() - td(days=1)).strftime(format='%Y%m%d')}")
        teams_json = teams_response.json()['events']
        for game in teams_json:
            for teams in game['competitions'][0]['competitors'] :
                if teams['team']['abbreviation'] == team:
                    team_id = teams['team']['id']

        return team_id

def get_team_logo(team, self):
    output_path = f'assets/images/{self.LEAGUE}/teams/{team}.png'
    team_id = get_team_id(team, self)
    url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/{self.LEAGUE.split('-')[-1].lower()}-college-basketball/teams/{team_id}'
    team_response = session.get(url=url)
    team_json = team_response.json()

    
    if len(team_json['team']['logos']) > 1:
        logo_url = team_json['team']['logos'][1]['href']
    else:
        logo_url = team_json['team']['logos'][0]['href']
    
    logo_response = session.get(url=logo_url)
    if logo_response.status_code == 200:
        Path(output_path).write_bytes(logo_response.content)
