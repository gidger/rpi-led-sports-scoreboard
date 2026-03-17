import requests
from datetime import datetime, timezone

JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"

# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def _current_season():
    """Returns the current year as the target F1 season."""
    return datetime.now(timezone.utc).year


def _fetch(url, timeout=10):
    """Simple GET wrapper with a shared timeout."""
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _standings_for_season(season):
    """Fetches raw StandingsLists for both driver and constructor endpoints."""
    try:
        d = _fetch(f"{JOLPICA_BASE}/{season}/driverstandings.json")
        driver_lists = d['MRData']['StandingsTable']['StandingsLists']

        c = _fetch(f"{JOLPICA_BASE}/{season}/constructorstandings.json")
        constructor_lists = c['MRData']['StandingsTable']['StandingsLists']

        return driver_lists, constructor_lists
    except Exception as e:
        print(f"F1 API Error (_standings_for_season {season}): {e}")
        return None, None


# ---------------------------------------------------------------------------
# Next Race
# ---------------------------------------------------------------------------

def get_next_race():
    """
    Returns a dict describing the next (or current-weekend) Grand Prix.
    Falls back to the most recent race if none remain this season.

    Keys: name, circuit_id, date, time, quali_date, quali_time,
          round, total_rounds, season
    """
    try:
        season = _current_season()
        data = _fetch(f"{JOLPICA_BASE}/{season}.json")
        races = data['MRData']['RaceTable']['Races']
        if not races:
            return None

        now = datetime.now(timezone.utc)
        total_rounds = len(races)

        # Find first race whose date is today or in the future
        for r in races:
            race_dt = datetime.strptime(
                f"{r['date']} {r.get('time', '00:00:00Z')}",
                "%Y-%m-%d %H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)

            if race_dt >= now:
                quali = r.get('Qualifying', {})
                return {
                    'season':        season,
                    'round':         int(r['round']),
                    'total_rounds':  total_rounds,
                    'name':          r['raceName'].replace('Grand Prix', 'GP').upper(),
                    'circuit_id':    r['Circuit']['circuitId'],
                    'circuit_name':  r['Circuit']['circuitName'],
                    'locality':      r['Circuit']['Location']['locality'],
                    'country':       r['Circuit']['Location']['country'],
                    'date':          r['date'],
                    'time':          r.get('time', '00:00:00Z').rstrip('Z'),
                    'quali_date':    quali.get('date'),
                    'quali_time':    quali.get('time', '00:00:00Z').rstrip('Z'),
                }

        # Season complete — return last race
        last = races[-1]
        return {
            'season':       season,
            'round':        int(last['round']),
            'total_rounds': total_rounds,
            'name':         last['raceName'].replace('Grand Prix', 'GP').upper(),
            'circuit_id':   last['Circuit']['circuitId'],
            'circuit_name': last['Circuit']['circuitName'],
            'locality':     last['Circuit']['Location']['locality'],
            'country':      last['Circuit']['Location']['country'],
            'date':         last['date'],
            'time':         last.get('time', '00:00:00Z').rstrip('Z'),
            'quali_date':   None,
            'quali_time':   None,
        }

    except Exception as e:
        print(f"F1 API Error (get_next_race): {e}")
        return None


# ---------------------------------------------------------------------------
# Driver Standings
# ---------------------------------------------------------------------------

def get_driver_standings(self, limit=20):
    """
    Returns a list of driver standing dicts, newest season with data first.
    Falls back to previous season if current season has no completed rounds.

    Each dict: pos, code, points, wins, constructor_id
    """
    season = _current_season()
    driver_lists, _ = _standings_for_season(season)

    # Fallback to previous season if current has no data yet
    if not driver_lists:
        print(f"F1: No {season} driver standings yet — falling back to {season - 1}.")
        driver_lists, _ = _standings_for_season(season - 1)

    if not driver_lists:
        return []

    standings = {
        'rank_method': 'Points',
        'abrv': 'Dri',
        'teams': []
    }

    raw = driver_lists[0]['DriverStandings'][:limit]
    for driver in raw :
        standings['teams'].append(
        {
            'rank': int(driver['position']),
            'team_abrv': driver['Driver'].get('code', driver['Driver']['familyName'][:3].upper()),
            'points': int(float(driver['points'])),
            'has_clinched': False
        }
    )

    return standings


# ---------------------------------------------------------------------------
# Constructor Standings
# ---------------------------------------------------------------------------

# Short display names for constructors. Add/update as rosters change.
_CONSTRUCTOR_NAMES = {
    'mercedes':          'MERCEDES',
    'red_bull':          'RED BULL',
    'ferrari':           'FERRARI',
    'mclaren':           'MCLAREN',
    'aston_martin':      'ASTON M.',
    'alpine':            'ALPINE',
    'williams':          'WILLIAMS',
    'alphatauri':        'AT',
    'rb':                'RB',
    'kick_sauber':       'SAUBER',
    'haas':              'HAAS',
    'racing_bulls':      'RB',
}


def get_constructor_standings(self, limit=10):
    """
    Returns a list of constructor standing dicts, newest season with data first.
    Falls back to previous season if current season has no completed rounds.

    Each dict: pos, name, short_name, constructor_id, points, wins
    """
    season = _current_season()
    _, constructor_lists = _standings_for_season(season)

    if not constructor_lists:
        print(f"F1: No {season} constructor standings yet — falling back to {season - 1}.")
        _, constructor_lists = _standings_for_season(season - 1)

    if not constructor_lists:
        return []

    standings = {
        'rank_method': 'Points',
        'abrv': 'Con',
        'teams': []
    }

    try:
        raw = constructor_lists[0]['ConstructorStandings'][:limit]
        for constructor in raw :
            standings['teams'].append(
                {
                    'rank':            int(constructor['position']),
                    'team_abrv':     _CONSTRUCTOR_NAMES.get(
                                        constructor['Constructor']['constructorId'][:5],
                                        constructor['Constructor']['name'][:5].upper()
                                    ),
                    'points':         int(float(constructor['points'])),
                    'has_clinched': False
                }
            )
        
        return standings

    except Exception as e:
        print(f"F1 API Error (get_constructor_standings parse): {e}")
        return []


# ---------------------------------------------------------------------------
# Qualifying / Race Results (for live scene)
# ---------------------------------------------------------------------------

def get_latest_qualifying(season=None, round_num='last'):
    """
    Returns a list of qualifying result dicts for the given round.
    Defaults to the most recently completed qualifying session.

    Each dict: pos, code, constructor_id, q1, q2, q3
    """
    if season is None:
        season = _current_season()
    try:
        data = _fetch(f"{JOLPICA_BASE}/{season}/{round_num}/qualifying.json")
        races = data['MRData']['RaceTable']['Races']
        if not races:
            return []

        raw = races[0]['QualifyingResults']
        return [
            {
                'pos':            int(r['position']),
                'code':           r['Driver'].get('code', r['Driver']['familyName'][:3].upper()),
                'constructor_id': r['Constructor']['constructorId'],
                'q1':             r.get('Q1', '--'),
                'q2':             r.get('Q2', '--'),
                'q3':             r.get('Q3', '--'),
            }
            for r in raw
        ]
    except Exception as e:
        print(f"F1 API Error (get_latest_qualifying): {e}")
        return []


def get_latest_race_results(season=None, round_num='last'):
    """
    Returns a list of race result dicts for the given round.
    Defaults to the most recently completed race.

    Each dict: pos, code, constructor_id, points, status, fastest_lap
    """
    if season is None:
        season = _current_season()
    try:
        data = _fetch(f"{JOLPICA_BASE}/{season}/{round_num}/results.json")
        races = data['MRData']['RaceTable']['Races']
        if not races:
            return []

        raw = races[0]['Results']
        results = []
        for r in raw:
            fl = r.get('FastestLap', {})
            results.append({
                'pos':            r.get('positionText', r['position']),
                'code':           r['Driver'].get('code', r['Driver']['familyName'][:3].upper()),
                'constructor_id': r['Constructor']['constructorId'],
                'points':         int(float(r['points'])),
                'status':         r.get('status', ''),
                'laps':           int(r.get('laps', 0)),
                'fastest_lap':    fl.get('Time', {}).get('time', '--'),
                'fastest_lap_rank': int(fl.get('rank', 99)),
            })
        return results

    except Exception as e:
        print(f"F1 API Error (get_latest_race_results): {e}")
        return []
