from .standings_scene import StandingsScene
from setup.matrix_setup import matrix
import data.mlb_data
from utils import data_utils

from datetime import datetime as dt
from time import sleep


class MLBStandingsScene(StandingsScene):
    """ Standings scene for the MLB. Contains functionality to pull standings data from MLB API, process as needed, and build+display images based on the result.
    This class extends the general Scene and StandingsScene classes. An object of this class type is created when the scoreboard is started.
    """

    def __init__(self):
        """ Defines the league as MLB. Used to identify the correct files when adding logos to images.
        First runs init from the generic GameScene class.
        """
        
        super().__init__()
        self.LEAGUE = 'MLB'


    def display_scene(self):
        """ Displays the scene on the matrix.
        """

        # Refresh config and load to settings key.
        self.settings = data_utils.read_yaml('config.yaml')['scene_settings'][self.LEAGUE.lower()]['standings']
        self.favourite_teams = data_utils.read_yaml('config.yaml')['favourite_teams'][self.LEAGUE.lower()]

        # Get current standings data.
        self.data = {
            'standings': data.mlb_data.get_standings()
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
            # Divisions.
            if type == 'division':
                for div in self.data['standings']['division']['divisions'].items(): # Get details needed for division standings.
                    div_details = div[1] # Needed to get to underlying team standings.
                    self.build_standings_image('division', div_details['abrv'], div_details['teams'], playoff_cutoff_soft=self.data['standings']['division']['playoff_cutoff_soft'])
                    self.display_standing_images()
            # Wildcard by conference.
            elif type == 'wildcard':
                for conf in self.data['standings']['wildcard']['conferences'].items():
                    conf_details = conf[1]
                    self.build_standings_image('wildcard', conf_details['abrv'], conf_details['teams'], playoff_cutoff_hard=self.data['standings']['wildcard']['playoff_cutoff_hard'], playoff_cutoff_soft=self.data['standings']['wildcard']['playoff_cutoff_soft'])
                    self.display_standing_images()
            # Conferences.
            elif type == 'conference':
                for conf in self.data['standings']['conference']['conferences'].items():
                    conf_details = conf[1]
                    self.build_standings_image('conference', conf_details['abrv'], conf_details['teams'])
                    self.display_standing_images()
            # Overall. Don't need to loop for this one as well... it's the whole league with no subdivisions.
            elif type == 'league':
                league_details = self.data['standings']['league']['leagues'][self.LEAGUE]
                self.build_standings_image('league', league_details['abrv'], league_details['teams'])
                self.display_standing_images()
            

    def display_standing_images(self):
        """ Displays standing images on the matrix w/ configured transitions.
        """

        self.transition_image(direction='in')
        self.scroll_standings_image()
        self.transition_image(direction='out', image_already_combined=False)
