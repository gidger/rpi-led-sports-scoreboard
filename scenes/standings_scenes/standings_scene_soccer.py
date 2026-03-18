from .standings_scene import StandingsScene
from setup.matrix_setup import matrix
import data.soccer_data
from utils import data_utils

from datetime import datetime as dt
from time import sleep


class SoccerStandingsScene(StandingsScene):
    """ Standings scene for the NBA. Contains functionality to pull standings data from NBA API, process as needed, and build+display images based on the result.
    This class extends the general Scene and StandingsScene classes. An object of this class type is created when the scoreboard is started.
    """

    def __init__(self, SoccerLeague):
        """ Defines the league as NBA. Used to identify the correct files when adding logos to images.
        First runs init from the generic GameScene class.
        """
        
        super().__init__()
        self.LEAGUE = SoccerLeague


    def display_scene(self):
        """ Displays the scene on the matrix.
        """

        # Refresh config and load to settings key.
        self.settings = data_utils.read_yaml('config.yaml')['scene_settings'][self.LEAGUE.lower()]['standings']
        self.favourite_teams = data_utils.read_yaml('config.yaml')['favourite_teams'][self.LEAGUE.lower()]

        # Get current standings data.
        self.data = {
            'standings': data.soccer_data.get_standings(self)
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
            # Conferences.
            if type == 'conference':
                for conf in self.data['standings']['conference']['conferences'].items():
                    conf_details = conf[1]
                    self.build_standings_image('conference', conf_details['abrv'], conf_details['teams'], playoff_cutoff_soft=self.data['standings']['conference']['playoff_cutoff_soft'], playoff_cutoff_hard=self.data['standings']['conference']['playoff_cutoff_hard'], relegation_cutoff=self.data['standings']['conference']['relegation_cutoff'])
                    self.display_standing_images()
            
            # League
            elif type == 'league':
                league_details = self.data['standings']['league']['leagues'][self.LEAGUE]
                if self.LEAGUE =='MLS' :
                    self.build_standings_image('league', league_details['abrv'], league_details['teams'])
                else :
                   self.build_standings_image('league', league_details['abrv'], league_details['teams'],  playoff_cutoff_soft=self.data['standings']['conference']['playoff_cutoff_soft'], playoff_cutoff_hard=self.data['standings']['conference']['playoff_cutoff_hard'], relegation_cutoff=self.data['standings']['conference']['relegation_cutoff'])
                self.display_standing_images()
            

    def display_standing_images(self):
        """ Displays standing images on the matrix w/ configured transitions.
        """

        self.transition_image(direction='in')
        self.scroll_standings_image()
        self.transition_image(direction='out', image_already_combined=False)
