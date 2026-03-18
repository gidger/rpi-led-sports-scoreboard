from .standings_scene import StandingsScene
from setup.matrix_setup import matrix
import data.f1_data
from utils import data_utils

from datetime import datetime as dt
from time import sleep


class F1StandingsScene(StandingsScene):
    """ Standings scene for the NBA. Contains functionality to pull standings data from NBA API, process as needed, and build+display images based on the result.
    This class extends the general Scene and StandingsScene classes. An object of this class type is created when the scoreboard is started.
    """

    def __init__(self, standings):
        """ Defines the league as NBA. Used to identify the correct files when adding logos to images.
        First runs init from the generic GameScene class.
        """
        
        super().__init__()
        self.LEAGUE = 'F1'
        self.F1_STANDINGS = standings


    def display_scene(self):
        """ Displays the scene on the matrix.
        """

        # Refresh config and load to settings key.
        self.settings = data_utils.read_yaml('config.yaml')['scene_settings'][self.LEAGUE.lower()]['standings']
        self.favourite_teams = data_utils.read_yaml('config.yaml')['favourite_teams'][self.LEAGUE.lower()]

        # Get current standings data.
        if self.F1_STANDINGS == 'driver' :
            self.data = {
                    'standings': data.f1_data.get_driver_standings(self, limit=10)
            }
        elif self.F1_STANDINGS == 'constructor' :
            self.data = {
                    'standings': data.f1_data.get_constructor_standings(self, limit=10)
            }

        # Display splash if enabled.
        if self.settings['splash']['display_splash']:
            # Build splash image, transition in, pause, transition out. 
            self.build_splash_image(dt.today().date())
            self.transition_image(direction='in', image_already_combined=True)
            sleep(self.settings['splash']['splash_display_duration'])
            self.transition_image(direction='out', image_already_combined=True)

        # For each standing type that should be displayed per config.yaml, build images and display.
        league_details = self.data['standings']
        self.build_standings_image('league', league_details['abrv'], league_details['teams'])
        self.display_standing_images()
            

    def display_standing_images(self):
        """ Displays standing images on the matrix w/ configured transitions.
        """

        self.transition_image(direction='in')
        self.scroll_standings_image()
        self.transition_image(direction='out', image_already_combined=False)
