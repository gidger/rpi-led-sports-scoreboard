from setup.session_setup import session
from datetime import datetime as dt
from datetime import timezone as tz
import json


key = '446521baf8c38984'  # API key for PWHL data. https://github.com/IsabelleLefebvre97/PWHL-Data-Reference

def get_games(date):
    """ Placeholder: Loads PWHL game data for the provided date.

    Args:
        date (date): Date that game data should be pulled for.

    Returns:
        list: List of dicts of game data. (Currently placeholder — implement API calls.)
    """
    
    # Create an empty list to hold the game dicts.
    games = []

    # Call the PWHL game API for the date specified and store the JSON results. First determine the current season.
    cur_season_id = get_season_id()
    url = f'https://lscluster.hockeytech.com/feed/index.php?client_code=pwhl&key={key}&feed=modulekit&view=scorebar&numberofdaysback=1&numberofdaysahead=1'
    games_response = session.get(url=url)
    games_json = games_response.json()['SiteKit']['Scorebar']

    # For each game, build a dict recording current game details.
    if games_json: # If games today. # TODO: validate what's returned when no games during range.
        for game in games_json:
            if game['SeasonID'] != str(cur_season_id) or game['Date'] != date.strftime('%Y-%m-%d'):
                continue    # Skip games not in current season or not on the requested date.
            
            # Append the dict to the games list.
            games.append({
                'game_id': game['ID'],
                'home_abrv': game['HomeCode'],
                'away_abrv': game['VisitorCode'],
                'home_score': int(game['HomeGoals']),
                'away_score': int(game['VisitorGoals']),
                'start_datetime_utc': dt.strptime(game['GameDateISO8601'], '%Y-%m-%dT%H:%M:%S%z').astimezone(tz=tz.utc),
                'start_datetime_local': dt.strptime(game['GameDateISO8601'], '%Y-%m-%dT%H:%M:%S%z').astimezone(tz=None), # Convert UTC to local time.
                'status': game['GameStatus'],
                'has_started': True if game['GameStatus'] in ['2', '3', '4'] else False, # 2 = In Progress, 3 = Unofficial Final,  4 = Final
                'period_num': int(game['Period']),
                'period_type': game['PeriodNameShort'], # Looks like there's nothing that notes if actively in shootout. Just that the game ended in shootout via GameStatusStringLong.
                'period_time_remaining': game['GameClock'],
                'is_intermission': True if (
                    game['Intermission'] == '1'
                    or (game['GameClock'] == '00:00' and game['GameStatus'] not in ['3', '4']) # Doesn't seem like the API sets Intermission flag consistently, so also check if time is 0 and game not final.
                ) else False,
                # Will set the remaining later, default to False and None for now.
                'home_team_scored': False,
                'away_team_scored': False,
                'scoring_team': None
            })
    
    # Sort games by ID to ensure consistent order.
    games = sorted(games, key=lambda x: x['game_id'])

    return games


def get_next_game(team):
    """ Placeholder: Loads next game details for the supplied PWHL team.

    Args:
        team (str): Team abbreviation to pull next game details for.

    Returns:
        dict or None: Dict of next game details or None if not found.
    """

    # Call the PWHL schedule API and store the JSON results. First determine the current season.
    cur_season_id = get_season_id()
    url = f'https://lscluster.hockeytech.com/feed/?client_code=pwhl&key={key}&feed=modulekit&view=schedule&season_id={cur_season_id}'
    schedule_response = session.get(url=url)
    schedule_json = schedule_response.json()['SiteKit']['Schedule']

    # Determine the future games.
    cur_datetime = dt.today().astimezone()
    cur_date = cur_datetime.date()
    upcoming_games = [game for  game in schedule_json if game['status'] in ('1','2')] # 1 = Scheduled, 2 = In Progress

    # Determine the next game for the team specified and return game details.
    for game in upcoming_games:
        if game['home_team_code'] == team or game['visiting_team_code'] == team:
            # Put together a dictionary with needed details.
            next_game = {
                'home_or_away': 'away' if game['home_team_code'] != team else 'home',
                'opponent_abrv': game['home_team_code'] if game['home_team_code'] != team else game['visiting_team_code'],
                'start_datetime_utc': dt.strptime(game['GameDateISO8601'], '%Y-%m-%dT%H:%M:%S%z').astimezone(tz=tz.utc),
                'start_datetime_local': dt.strptime(game['GameDateISO8601'], '%Y-%m-%dT%H:%M:%S%z').astimezone(tz=None), # Convert UTC to local time.
                'is_today': True if dt.strptime(game['GameDateISO8601'], '%Y-%m-%dT%H:%M:%S%z').astimezone(tz=None).date() == cur_date or dt.strptime(game['GameDateISO8601'], '%Y-%m-%dT%H:%M:%S%z').astimezone(tz=None) < cur_datetime else False, # TODO: clean this up. Needed in case game is still going when date rolls over.
                'has_started': True if game['status'] in ['2', '3', '4'] else False # 2 = In Progress, 3 = Unofficial Final,  4 = Final
            }

            return(next_game)

    # If no next game found, return None.
    return None


def get_standings():
    """ Loads current PWHL standings.

    Returns:
        dict: Dict containing all standings by each category.
    """

    # Call the PWHL standings API and store the JSON results. First determine the current season.
    cur_season_id = get_season_id()
    url = f'https://lscluster.hockeytech.com/feed/index.php?client_code=pwhl&key={key}&feed=modulekit&view=statviewtype&stat=conference&type=standings&season_id={cur_season_id}'
    standings_response = session.get(url=url)
    standings_json = standings_response.json()['SiteKit']['Statviewtype'][1:] # 0th element is metadata.

    # Set up structure of the returned dict.
    standings = {
        'retrieved_on': dt.now().astimezone(),
        'league': {
            'PWHL': { # Exists to match structure needed for other standing types.
                'rank_method': 'Points',
                'playoff_cutoff_hard': 4,
                'team_standings': [] # Will be populated w/ the API results.
            }
        }
    }

    # Populate the team lists w/ dicts containing details of each team.
    for team in standings_json:
        # Overall league.
        standings['league']['PWHL']['team_standings'].append({
            'team_abrv': team['team_code'],
            'rank': int(team['overall_rank']),
            'points': int(team['points']),
            'has_clinched': True if team['clinched_playoff_spot'] == '1' else False
        })

    return standings


def get_season_id():
    """ Determines the PWHL season ID.

    Returns:
        int: current season ID.
    """

    # Note the current datetime.
    cur_datetime = dt.today().astimezone()
    cur_date = dt.today().astimezone().date()

    # Call the PWHL seasons API and store the JSON results.
    url = f'https://lscluster.hockeytech.com/feed/index.php?client_code=pwhl&key={key}&feed=modulekit&view=seasons'
    seasons_response = session.get(url=url)
    seasons_json = seasons_response.json()['SiteKit']['Seasons']

    # The API returns the current season, but as we don't want preseason games, we'll need to parse further.
    for season in seasons_json:
        # Determine the current season. If preseason, return the next season ID.
        if season['start_date'] <= cur_date.strftime('%Y-%m-%d') <= season['end_date']:
            # TODO: Validate pre and post season behavior.
            if 'Preseason' not in season['season_name']:
                return int(season['season_id'])
            else:
                return int(season['season_id']) + 1