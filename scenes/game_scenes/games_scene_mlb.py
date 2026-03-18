from .games_scene import GamesScene
from setup.matrix_setup import matrix
import data.mlb_data
from utils import data_utils, date_utils

from datetime import datetime as dt
from time import sleep


class MLBGamesScene(GamesScene):
    """ Game scene for the MLB. Contains functionality to pull data from MLB API, parse, and build+display specific images based on the result.
    This class extends the general Scene and GameScene classes. An object of this class type is created when the scoreboard is started.
    """

    def __init__(self):
        """ Defines the league as MLB. Used to identify the correct files when adding logos to images.
        First runs init from the generic GameScene class.
        """
        
        super().__init__()
        self.LEAGUE = 'MLB'


    def display_scene(self):
        """ Displays the scene on the matrix.
        Includes logic on which image to build, when to display, etc.
        """

        # Refresh config and load to settings key.
        self.settings = data_utils.read_yaml('config.yaml')['scene_settings'][self.LEAGUE.lower()]['games']
        self.alt_logos = data_utils.read_yaml('config.yaml')['alt_logos'][self.LEAGUE.lower()] if data_utils.read_yaml('config.yaml')['alt_logos'][self.LEAGUE.lower()] else {} # Note the teams with an alternative logo per config.yaml.

        # Determine which days should be displayed. Will generate a list with one or two elements. Two means rollover time and yesterdays games should be displayed.
        dates_to_display = date_utils.determine_dates_to_display_games(self.settings['rollover']['rollover_start_time_local'], self.settings['rollover']['rollover_end_time_local'])
        display_yesterday = True if len(dates_to_display) == 2 else False # Will have to display yesterdays games if dates_to_display has 2 elements.

        # If in rollover time, and the data for previous day hasn't been saved / is from a different date than needed, then pull it.
        # This will ensure we don't need to pull the previous day data (that doesn't change) every loop.
        if display_yesterday:
            if (hasattr(self, 'data_previous_day') and self.data_previous_day['saved_date'] != dates_to_display[0]) or not hasattr(self, 'data_previous_day'):
                self.data_previous_day = {
                    'saved_date': dates_to_display[0], # Note the previous date.
                    'games': data.mlb_data.get_games(dates_to_display[0]) # Get data for previous date.
                }
        
        # Get current day game data. Save this for future reference.
        self.data = {
            'games_previous_pull': self.data['games'] if hasattr(self, 'data') else None, # If this is the first time this is run, we'd expect self.data to not exist.
            'games': data.mlb_data.get_games(dates_to_display[-1]), # Get data for current day. Current day will always be the last element of dates_to_display.
        }

        # If there are games to display from yesterday (and setting is enabled), build and display splash image (if enabled), then images for those games.
        if display_yesterday and self.settings['rollover']['show_completed_games_until_rollover_end_time']:
            if self.settings['splash']['display_splash']:
                self.display_splash_image(len(self.data_previous_day['games']), date=dates_to_display[0])
            self.display_game_images(self.data_previous_day['games'], date=dates_to_display[0])

        # For the current day's games, note if any runs were scored since the last data pull.
        if self.data['games_previous_pull']: # Only applicable if there's a previous copy to compare to.
            for game in self.data['games']:
                if game['status'] not in ['FUT', 'PRE']: # Not applicable if the game hasn't started yet.
                    # Match games between data pulls.
                    matched_game = next(filter(lambda x: x['game_id'] == game['game_id'], self.data['games_previous_pull']))

                    if matched_game['status'] not in ['FUT', 'PRE']: # Not applicable if the game hasn't started yet in the previous pull.
                        # Determine if either team scored and set keys accordingly.
                        game['away_team_scored'] = True if game['away_score'] > matched_game['away_score'] else False
                        game['home_team_scored'] = True if game['home_score'] > matched_game['home_score'] else False
                        
                        if game['away_team_scored'] and game['home_team_scored']:
                            game['scoring_team'] = 'both'
                        elif game['away_team_scored']:
                            game['scoring_team'] = 'away'
                        elif game['home_team_scored']:
                            game['scoring_team'] = 'home'
                    
        # Display splash (if enabled) for current day.
        if self.settings['splash']['display_splash']:
            self.display_splash_image(len(self.data['games']), date=dates_to_display[-1])
        
        # Display game image(s) for current day.
        self.display_game_images(self.data['games'], date=dates_to_display[-1])


    def display_splash_image(self, num_games, date):
        """ Builds and displays splash screen for games on date.

        Args:
            num_games (int): Num of games happening on date.
            date (date): Date of games.
        """
        
        # Build splash image, transition in, pause, transition out. 
        self.build_splash_image(num_games, date)
        self.transition_image(direction='in', image_already_combined=True)
        sleep(self.settings['splash']['splash_display_duration'])
        self.transition_image(direction='out', image_already_combined=True)
                                                                                               

    def display_game_images(self, games, date=None):
        """ Builds and displays images on the matrix for each game in games.

        Args:
            games (list): List of game dicts. Each element has all details for a single game.
            date (date, optional): Date of games. Only used to build 'no games' image when there's... well, no games on that data. Defaults to None.
        """
        
        # If there's any games to display, loop through them and build the appropriate images.
        if games:
            for game in games:
                # If the game has yet to begin, build the game not started image.
                if game['status'] in ['FUT', 'PRE']:
                    self.build_game_not_started_image(game)

                # If the game is over, build the final score image.
                elif game['status'] in ['OFF', 'FINAL']:
                    self.build_game_complete_image(game)

                # Otherwise, the game is in progress. Build the game in progress screen.
                elif game['status'] in ['LIVE', 'CRIT']:
                    self.build_game_in_progress_image(game)
                else:
                    print(f"Unexpected game status encountered from API: {game['status']}.")

                # Transition the image in on the matrix.
                self.transition_image(direction='in')

                # If a run was scored, do score fade animation (if enabled).
                if self.settings['score_alerting']['score_coloured'] and self.settings['score_alerting']['score_fade_animation']:
                    if game['scoring_team']:
                        self.fade_score_change(game)
                
                # Hold image for calculated duration and transition out.
                sleep(self.settings['game_display_duration'])
                self.transition_image(direction='out')
        
        # If there's no games to display, and splash is disabled, build and display the no games image.
        elif not self.settings['splash']['display_splash']:
            self.build_no_games_image(date)
            self.transition_image(direction='in', image_already_combined=True)
            sleep(self.settings['game_display_duration'])
            self.transition_image(direction='out', image_already_combined=True)


    def add_playing_period_to_image(self, game):
        """ Adds current playing inning to the centre image.
        This exists within the specific league class due to huge differences in playing periods between sports (periods, quarters, innings, etc.).

        Args:
            game (dict): Dictionary with all details of a specific game.
        """
        
        # TODO: Add inning display logic here. May show inning number and state (Top/Bottom).
        pass


    def add_final_playing_period_to_image(self, game):
        """ Adds final playing inning to the centre image if game ended in extra innings.

        Args:
            game (dict): Dictionary with all details of a specific game.
        """

        # TODO: Add final inning display logic if needed.
        pass


    def should_display_time_remaining_in_playing_period(self, game):
        """ Determines if the time remaining in the playing inning should be added to the centre image.

        Args:
            game (dict): Dictionary with all details of a specific game.

        Returns:
            Bool: If the time remaining in the playing inning should be added to the centre image (True) or not (False).
        """

        # TODO: Determine based on game state if inning info should be displayed
        return False
