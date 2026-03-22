from .standings_scene import StandingsScene
from setup.matrix_setup import matrix
import data.nba_data
from utils import data_utils

from datetime import datetime as dt
from time import sleep


class NBAStandingsScene(StandingsScene):
    """ Standings scene for the NBA. Contains functionality to pull standings data from NBA API, process as needed, and build+display images based on the result.
    This class extends the general Scene and StandingsScene classes. An object of this class type is created when the scoreboard is started.
    """

    def __init__(self):
        """ Defines the league as NBA. Used to identify the correct files when adding logos to images.
        First runs init from the generic GameScene class.
        """
        
        super().__init__()
        self.LEAGUE = 'NBA'

        # Add additional colour needed.
        self.COLOURS.update({
            'sidebar_highlight': (212, 54, 47) # NBA red.
        })


    def display_scene(self):
        """ Displays the scene on the matrix.
        """

        # Refresh config and load to settings key.
        self.settings = data_utils.read_yaml('config.yaml')['scene_settings'][self.LEAGUE.lower()]['standings']
        self.favourite_teams = data_utils.read_yaml('config.yaml')['favourite_teams'][self.LEAGUE.lower()]

        # Get current standings data.
        self.data = {
            'standings': data.nba_data.get_standings()
        }

        # Display splash if enabled.
        if self.settings['splash']['display_splash']:
            # Build splash image, transition in, pause, transition out. 
            self.build_splash_image(dt.today().date())
            self.transition_image(direction='in', image_already_combined=True)
            sleep(self.settings['splash']['splash_display_duration'])
            self.transition_image(direction='out', image_already_combined=True)

        # For each standing type that should be displayed per config.yaml, build images and display.
        for type in self.settings['display_for']:
            # Check if standings data exists for the type before trying to build images.
            standing_details = self.data['standings'].get(type)
            if standing_details:
                # Loop over each division/conference/whatever.
                for sub_standing_details in standing_details.values():
                    self.build_standings_image(sub_standing_details)
                    self.display_standing_images()
            

    def display_standing_images(self):
        """ Displays standing images on the matrix w/ configured transitions.
        """

        self.transition_image(direction='in')
        self.scroll_standings_image()
        self.transition_image(direction='out', image_already_combined=False)