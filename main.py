from scenes.game_scenes.games_scene_nhl import NHLGamesScene
from scenes.fav_team_next_game_scenes.fav_team_next_game_scene_nhl import NHLFavTeamNextGameScene
from scenes.standings_scenes.standings_scene_nhl import NHLStandingsScene

from scenes.game_scenes.games_scene_nba import NBAGamesScene
from scenes.fav_team_next_game_scenes.fav_team_next_game_scene_nba import NBAFavTeamNextGameScene
from scenes.standings_scenes.standings_scene_nba import NBAStandingsScene

from scenes.game_scenes.games_scene_ncaa import NCAAGamesScene
from scenes.fav_team_next_game_scenes.fav_team_next_game_scene_ncaa import NCAAFavTeamNextGameScene

from scenes.game_scenes.games_scene_pwhl import PWHLGamesScene
from scenes.fav_team_next_game_scenes.fav_team_next_game_scene_pwhl import PWHLFavTeamNextGameScene
from scenes.standings_scenes.standings_scene_pwhl import PWHLStandingsScene

from scenes.game_scenes.games_scene_soccer import SoccerGamesScene
from scenes.fav_team_next_game_scenes.fav_team_next_game_scene_soccer import SoccerFavTeamNextGameScene
from scenes.standings_scenes.standings_scene_soccer import SoccerStandingsScene

from scenes.f1_scenes.f1_race_preview import F1RacePreviewScene
from scenes.f1_scenes.f1_race_weekend import F1RaceWeekendScene
from scenes.f1_scenes.f1_next_race import F1NextRaceScene
from scenes.standings_scenes.standings_scene_f1 import F1StandingsScene

from scenes.standings_scenes.standings_scene_f1 import F1StandingsScene
from setup.matrix_setup import matrix, determine_matrix_brightness
from utils import data_utils


def run_scoreboard():
    # Instantiate objects for each of the "scenes" (i.e., visual ideas) supported.
    scene_mapping = {
        'nhl_games': NHLGamesScene(),
        'nhl_fav_team_next_game': NHLFavTeamNextGameScene(),
        'nhl_standings': NHLStandingsScene(),
        
        'nba_games': NBAGamesScene(),
        'nba_fav_team_next_game': NBAFavTeamNextGameScene(),
        'nba_standings': NBAStandingsScene(),

        'ncaa_mens_games': NCAAGamesScene('NCAA-MENS'),
        'ncaa_mens_fav_team_next_game': NCAAFavTeamNextGameScene('NCAA-MENS'),

        'ncaa_womens_games': NCAAGamesScene('NCAA-WOMENS'),
        'ncaa_womens_fav_team_next_game': NCAAFavTeamNextGameScene('NCAA-WOMENS'),
        
        'pwhl_games': PWHLGamesScene(),
        'pwhl_fav_team_next_game': PWHLFavTeamNextGameScene(),
        'pwhl_standings': PWHLStandingsScene(),

        'mls_games': SoccerGamesScene('MLS'),
        'mls_fav_team_next_game': SoccerFavTeamNextGameScene('MLS'),
        'mls_standings': SoccerStandingsScene('MLS'),

        # Premier League
        'epl_games': SoccerGamesScene('EPL'),
        'epl_fav_team_next_game': SoccerFavTeamNextGameScene('EPL'),
        'epl_standings': SoccerStandingsScene('EPL'),

        # La Liga
        'laliga_games': SoccerGamesScene('LL'),
        'laliga_fav_team_next_game': SoccerFavTeamNextGameScene('LL'),
        'laliga_standings': SoccerStandingsScene('LL'),

        # Bundesliga
        'bundesliga_games': SoccerGamesScene('BL'),
        'bundesliga_fav_team_next_game': SoccerFavTeamNextGameScene('BL'),
        'bundesliga_standings': SoccerStandingsScene('BL'),

        # Serie A
        'seriea_games': SoccerGamesScene('SA'),
        'seriea_fav_team_next_game': SoccerFavTeamNextGameScene('SA'),
        'seriea_standings': SoccerStandingsScene('SA'),

        # Ligue 1
        'ligue1_games': SoccerGamesScene('L1'),
        'ligue1_fav_team_next_game': SoccerFavTeamNextGameScene('L1'),
        'ligue1_standings': SoccerStandingsScene('L1'),

        'concacaf_games': SoccerGamesScene('CONCACAF'),
        'concacaf_fav_team_next_game': SoccerFavTeamNextGameScene('CONCACAF'),

        'f1_race_preview':        F1RacePreviewScene(),
        'f1_race_weekend':        F1RaceWeekendScene(),
        'f1_next_race':           F1NextRaceScene(),
        'f1_driver_standings':    F1StandingsScene('driver'),
        'f1_constructor_standings': F1StandingsScene('constructor')
    }

    # Infinite loop.
    while True:
        # Determine the order scenes should be displayed per config.yaml.
        scene_order = data_utils.read_yaml('config.yaml')['scene_order']

        # Set matrix brightness.
        matrix.brightness = determine_matrix_brightness()

        # Display each scene in the order specified above.
        for scene in scene_order:
            scene_mapping[scene].display_scene()

# Entrypoint.
if __name__ == '__main__':
    run_scoreboard()
