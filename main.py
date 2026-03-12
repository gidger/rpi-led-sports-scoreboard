from scenes.game_scenes.games_scene_nhl import NHLGamesScene
from scenes.fav_team_next_game_scenes.fav_team_next_game_scene_nhl import NHLFavTeamNextGameScene
from scenes.standings_scenes.standings_scene_nhl import NHLStandingsScene

from scenes.game_scenes.games_scene_nba import NBAGamesScene
from scenes.fav_team_next_game_scenes.fav_team_next_game_scene_nba import NBAFavTeamNextGameScene
from scenes.standings_scenes.standings_scene_nba import NBAStandingsScene

from scenes.game_scenes.games_scene_pwhl import PWHLGamesScene
from scenes.fav_team_next_game_scenes.fav_team_next_game_scene_pwhl import PWHLFavTeamNextGameScene
from scenes.standings_scenes.standings_scene_pwhl import PWHLStandingsScene

from scenes.game_scenes.games_scene_mls import MLSGamesScene
from scenes.fav_team_next_game_scenes.fav_team_next_game_scene_mls import MLSFavTeamNextGameScene

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
        
        'pwhl_games': PWHLGamesScene(),
        'pwhl_fav_team_next_game': PWHLFavTeamNextGameScene(),
        'pwhl_standings': PWHLStandingsScene(),

        'mls_games': MLSGamesScene(),
        'mls_fav_team_next_game': MLSFavTeamNextGameScene()
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
