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

    # Call the MLB game API for the date specified and store the JSON results.
    # TODO: Implement MLB API call for games on the provided date.
    games_json = []

    # For each game, build a dict recording current game details.
    if games_json: # If games today.
        for game in games_json:
            games.append({
                'game_id': None,  # TODO: Extract from API
                'home_abrv': None,  # TODO: Extract from API
                'away_abrv': None,  # TODO: Extract from API
                'home_score': None,  # TODO: Extract from API
                'away_score': None,  # TODO: Extract from API
                'start_datetime_utc': None,  # TODO: Extract from API
                'start_datetime_local': None,  # TODO: Extract from API
                'status': None,  # TODO: Extract from API
                'has_started': False,  # TODO: Extract from API
                'inning_num': None,  # TODO: Extract from API (placeholder for period)
                'inning_state': None,  # TODO: Extract from API (Top/Bottom)
                'period_time_remaining': None,  # TODO: Extract from API (outs, balls, strikes)
                'is_intermission': False,
                # Will set the remaining later, default to False and None for now.
                'home_team_scored': False,
                'away_team_scored': False,
                'scoring_team': None
            })

    return games


def get_next_game(team):
    """ Loads next game details for the supplied MLB team.
    If the team is currently playing, will return details of the current game.

    Args:
        team (str): Team abbreviation to pull next game details for.

    Returns:
            dict: Dict of next game details.
    """
    
    # Note the current datetime.
    cur_datetime = dt.today().astimezone()
    cur_date = dt.today().astimezone().date()

    # Call the MLB schedule API for the team specified and store the JSON results.
    # TODO: Implement MLB API call for team schedule.
    schedule_json = []

    # Filter results to games that have not already concluded. Get the 0th element, the next game.
    upcoming_games = []  # TODO: Filter schedule_json for upcoming games
    next_game_details = upcoming_games[0] if len(upcoming_games) > 0 else None

    if next_game_details:
        # Put together a dictionary with needed details.
        next_game = {
            'home_or_away': None,  # TODO: Extract from API
            'opponent_abrv': None,  # TODO: Extract from API
            'start_datetime_utc': None,  # TODO: Extract from API
            'start_datetime_local': None,  # TODO: Extract from API
            'is_today': False,  # TODO: Determine from API
            'has_started': False  # TODO: Determine from API
        }
        return(next_game)
    
    # If no next game found, return None.
    return None


def get_standings():
    """ Loads current MLB standings by division, wildcard, conference, and overall league.

    Returns:
        dict: Dict containing all standings by each category.
    """

    # Call the MLB standings API and store the JSON results.
    # TODO: Implement MLB API call for standings.
    standings_json = {}

    standings = {
        'division': {
            'divisions': {},
            'playoff_cutoff_soft': None
        },
        'wildcard': {
            'conferences': {},
            'playoff_cutoff_hard': None,
            'playoff_cutoff_soft': None
        },
        'conference': {
            'conferences': {}
        },
        'league': {
            'leagues': {
                'MLB': {
                    'abrv': 'MLB',
                    'teams': []
                }
            }
        }
    }

    # TODO: Parse standings_json and populate standings dict structure

    return standings
