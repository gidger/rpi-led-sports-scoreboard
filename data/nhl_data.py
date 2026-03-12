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
    url = 'https://api-web.nhle.com/v1/score/'
    games_response = session.get(url=f"{url}{date.strftime(format='%Y-%m-%d')}")
    games_json = games_response.json()['games']

    # For each game, build a dict recording current game details.
    if games_json: # If games today.
        for game in games_json:
            # Append the dict to the games list. We only want to get regular season (gameType = 2) and playoff (3) games.
            # Note that 19 and 20 may need to be included. These were used for the 4 Nations Face-Off round robin & finals and will be evaluated again in the future.
            if game['gameType'] in [2, 3]:
                games.append({
                    'league': 'NHL',
                    'game_id': game['id'],
                    'home_abrv': game['homeTeam']['abbrev'],
                    'away_abrv': game['awayTeam']['abbrev'],
                    'home_score': game['homeTeam'].get('score'), # Doesn't exist until game starts.
                    'away_score': game['awayTeam'].get('score'),
                    'start_datetime_utc': dt.strptime(game['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc),
                    'start_datetime_local': dt.strptime(game['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None), # Convert UTC to local time.
                    'status': game['gameState'],
                    'has_started': True if game['gameState'] in ['LIVE', 'CRIT', 'OFF', 'FINAL'] else False,
                    'period_num': game.get('period'), # Doesn't until game starts.
                    'period_type': game.get('periodDescriptor', {}).get('periodType'), # periodDescriptor doesn't exist until game starts.
                    'period_time_remaining': game.get('clock', {}).get('timeRemaining'), # clock doesn't exist until game starts.
                    'is_intermission': game.get('clock', {}).get('inIntermission'),
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
        team (str): Three char abbreviation of the team to pull next game details for.

    Returns:
            dict: Dict of next game details.
    """
    
    # Note the current datetime.
    cur_datetime = dt.today().astimezone()
    cur_date = dt.today().astimezone().date()

    # Call the NHL schedule API for the team specified and store the JSON results.
    url = f'https://api-web.nhle.com/v1/club-schedule-season/{team}/now'
    schedule_response = session.get(url=url)
    schedule_json = schedule_response.json()['games']

    # Filter results to games that have not already concluded. Get the 0th element, the next game.
    upcoming_games = [game for game in schedule_json if game['gameState'] in ('FUT', 'PRE', 'LIVE', 'CRIT')]
    next_game_details = upcoming_games[0] if len(upcoming_games) > 0 else None

    if next_game_details:
        # Put together a dictionary with needed details.
        next_game = {
            'home_or_away': 'away' if next_game_details['homeTeam']['abbrev'] != team else 'home',
            'opponent_abrv': next_game_details['homeTeam']['abbrev'] if next_game_details['homeTeam']['abbrev'] != team else next_game_details['awayTeam']['abbrev'],
            'start_datetime_utc': dt.strptime(next_game_details['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc),
            'start_datetime_local': dt.strptime(next_game_details['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None),
            'is_today': True if dt.strptime(next_game_details['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None).date() == cur_date or dt.strptime(next_game_details['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None) < cur_datetime else False, # TODO: clean this up. Needed in case game is still going when date rolls over.
            'has_started': True if next_game_details['gameState'] in ('LIVE', 'CRIT') else False
        }
        return(next_game)
    
    # If no next game found, return None.
    return None


def get_standings():
    """ Loads current NHL standings by division, wildcard, conference, and overall league.

    Returns:
        dict: Dict containing all standings by each category.
    """

    # Call the NHL standings API and store the JSON results.
    url = 'https://api-web.nhle.com/v1/standings/now'
    standings_response = session.get(url=url)
    standings_json = standings_response.json()['standings']

    # Set up structure of the returned dict.
    # Teams lists will be populated w/ the API results.
    standings = {
        'rank_method': 'Points',
        'division': {
            'playoff_cutoff_soft': 3, # Notes how many teams from each div make the playoffs before wildcards.
            'divisions': {
                'Atlantic': {
                    'abrv': 'Atl',
                    'teams': []
                },
                'Metropolitan': {
                    'abrv': 'Met',
                    'teams': []
                },
                'Central': {
                    'abrv': 'Cen',
                    'teams': []
                },
                'Pacific': {
                    'abrv': 'Pac',
                    'teams': []
                }
            }
         },

        'wildcard': {
            'playoff_cutoff_hard': 8, # Not exactly true... but will help build the images. Total num of playoff bound teams.
            'playoff_cutoff_soft': 6,
            'conferences': {
                'Eastern': {
                    'abrv': 'Est',
                    'teams': []
                },
                'Western': {
                    'abrv': 'Wst',
                    'teams': []
                }
            }
        },

        # Structure for conferences and league is not the best, but want to leave open in case of future divisional changes (e.g., return to conference based playoff thresholds).
        'conference': {
            'conferences': {
                'Eastern': {
                    'abrv': 'Est',
                    'teams': []
                },
                'Western': {
                    'abrv': 'Wst',
                    'teams': []
                },
            }
        },

        'league': {
            'leagues': {
                'NHL': {
                    'abrv': 'All',
                    'teams': []
                }
            }
        }
    }

    # Populate the team lists w/ dicts containing details of each team.
    # API returns teams in overall standing order, so generally won't have to sort.
    for team in standings_json:
        # Divisions.
        standings['division']['divisions'][team['divisionName']]['teams'].append(
            {
                'team_abrv': team['teamAbbrev']['default'],
                'rank': team['divisionSequence'],
                'points': team['points'],
                'has_clinched': True if hasattr(team, 'clinchIndicator') else False # The clinchIndicator key will only exist for teams that have clinched.
            }
        )

        # Wildcard by conference.
        standings['wildcard']['conferences'][team['conferenceName']]['teams'].append(
            {
                'team_abrv': team['teamAbbrev']['default'],
                'rank': team['wildcardSequence'] if team['wildcardSequence'] != 0 else team['divisionAbbrev'] + str(team['divisionSequence']), # Top 3 teams will have a wildcardSequence of 0.
                # Rank helper will allow us to group top 3 teams in each div so they appear together at the top of the WC standings.
                'rank_helper': 'W' + str(team['wildcardSequence']).zfill(2) if team['wildcardSequence'] != 0 else team['divisionAbbrev'] + str(team['divisionSequence']),
                'points': team['points'],
                'has_clinched': True if hasattr(team, 'clinchIndicator') else False
            }
        )

        # Conference.
        standings['conference']['conferences'][team['conferenceName']]['teams'].append(
            {
                'team_abrv': team['teamAbbrev']['default'],
                'rank': team['conferenceSequence'],
                'points': team['points'],
                'has_clinched': True if hasattr(team, 'clinchIndicator') else False
            }
        )

        # Overall league.
        standings['league']['leagues']['NHL']['teams'].append(
            {
                'team_abrv': team['teamAbbrev']['default'],
                'rank': team['leagueSequence'],
                'points': team['points'],
                'has_clinched': True if hasattr(team, 'clinchIndicator') else False
            }
        )

    # Sort team list within wildcard to correctly group top three teams in each division.
    for con in standings['wildcard']['conferences'].values():
        con['teams'] = sorted(con['teams'], key=lambda d: d['rank_helper'])

    return standings