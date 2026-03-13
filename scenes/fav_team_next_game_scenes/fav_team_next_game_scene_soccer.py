from .fav_team_next_game_scene import FavTeamNextGameScene
from setup.matrix_setup import matrix
import data.soccer_data
from utils import data_utils

from datetime import datetime as dt
from time import sleep


class SoccerFavTeamNextGameScene(FavTeamNextGameScene):
    """ Favourite team next game scene for the soccer league of choice. Contains functionality to pull schedule data from ESPN API, parse, and build+display images based on the result.
    This class extends the general Scene and FavTeamNextGameScene classes. An object of this class type is created when the scoreboard is started.
    """

    def __init__(self, SoccerLeague):
        """ Defines the league as input league. Used to identify the correct files when adding logos to images.
        First runs init from the generic GameScene class.
        """
        
        super().__init__()
        self.LEAGUE = SoccerLeague

    def display_scene(self):
        """ Displays the scene on the matrix.
        """

        # Refresh config and load to settings key.
        self.settings = data_utils.read_yaml('config.yaml')['scene_settings'][self.LEAGUE.lower()]['fav_team_next_game']
        self.favourite_teams = data_utils.read_yaml('config.yaml')['favourite_teams'][self.LEAGUE.lower()]
        self.alt_logos = data_utils.read_yaml('config.yaml')['alt_logos'][self.LEAGUE.lower()] if data_utils.read_yaml('config.yaml')['alt_logos'][self.LEAGUE.lower()] else {} # Note the teams with an alternative logo per config.yaml.

        # Determine next game for each fav team per config.yaml. Build images and display.
        if self.favourite_teams:
            for team in self.favourite_teams:
                next_game_details = data.soccer_data.get_next_game(team, self)
                
                if next_game_details:
                    # If a game is in progress, and display_if_in_progress is False, exit without displaying anything.
                    if next_game_details['is_today'] and next_game_details['has_started'] and not self.settings['display_if_in_progress']:
                        continue # Move on to the next fav team.
                    
                    # Otherwise, build image and display.
                    else:
                        self.build_next_game_image(team, next_game_details)
                        self.transition_image(direction='in')
                        sleep(self.settings['display_duration'])
                        self.transition_image(direction='out')