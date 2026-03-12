from ..scene import Scene
from setup.matrix_setup import matrix, matrix_options
from utils import image_utils

from PIL import Image, ImageDraw
from time import sleep
import math


class GamesScene(Scene):
    """ Generic game scene, regardless of league/sport. Contains functionality to build score, no game today, etc. images and display them on the matrix.
    This class extends the general Scene class and is extended by those of specific leagues. An object of this class type is never created directly.
    """
    
    def __init__(self):
        """ Creates Image objects to be displayed on the matrix and ImageDraw objects allowing us to add logos, text, etc. to each image.
        First runs init from generic Scene class.
        """

        super().__init__()

        # Image objects.
        self.images = {
            # Helper images that each tackle of portion of the full image.
            'left':     Image.new('RGB', (40, 30)), # 21 of 40 cols will be visible on matrix (cols 0-20) when not moving. This leaves a col of buffer before the centre.
            'centre':   Image.new('RGB', (20, 30)),
            'right':    Image.new('RGB', (40, 30)), # 21 of 40 cols will be visible on matrix (cols 43-63) when not moving. This leaves a col of buffer after the centre.
            # Full image that gets displayed to matrix.
            'full':     Image.new('RGB', (matrix_options.cols, matrix_options.rows))
        }

        # ImageDraw objects associated with each of the above Image objects.
        self.draw = {
            'left':     ImageDraw.Draw(self.images['left']),
            'centre':   ImageDraw.Draw(self.images['centre']),
            'right':    ImageDraw.Draw(self.images['right']),
            'full':     ImageDraw.Draw(self.images['full'])
        }


    def build_splash_image(self, num_games, date):
        """ Builds splash screen image.
        Includes league logo, date, and number of games on that date.

        Args:
            num_games (int): Number of games on the provided date.
            date (date): Date to display.
        """

         # First, add the league logo image.
        self.add_league_logo_to_image()

        # Add 'Games' and a horizontal line.
        self.draw['full'].text((33, 0), 'Games', font=self.FONTS['med_bold'], fill=self.COLOURS['white'])
        self.draw['full'].line([(32, 10), (62, 10)], fill=self.COLOURS['white'])

        # Determine horizontal location, and add the number of games.
        num_games_col = 45 if len(str(num_games)) == 1 else 42
        self.draw['full'].text((num_games_col, 12), str(num_games), font=self.FONTS['med'], fill=self.COLOURS['white'])

        # Note the month (3 char) and day number.
        month = date.strftime('%b')
        day = date.strftime('%-d')

        # Determine horizontal location, and add the date.
        month_col = 37 if len(day) == 1 else 35
        self.draw['full'].text((month_col, 22), month, font=self.FONTS['sm'], fill=self.COLOURS['white'])
        day_col = 53 if len(day) == 1 else 51
        self.draw['full'].text((day_col, 22), day, font=self.FONTS['sm'], fill=self.COLOURS['white'])


    def build_no_games_image(self, date):
        """ Builds image for when there's no games on the specified date.
        Includes league logo, 'No Games' message, and the date with no games.

        Args:
            date (date): Date with no games, to be added to the image.
        """
        
        # First, add the league logo image.
        self.add_league_logo_to_image()

        # Add the text 'No Games' and the date to the image.
        self.draw['full'].text((31, 0), 'No', font=self.FONTS['med'], fill=self.COLOURS['white'])
        self.draw['full'].text((31, 10), 'Games', font=self.FONTS['med'], fill=self.COLOURS['white'])
        self.draw['full'].text((31, 21), date.strftime('%b %-d'), font=self.FONTS['sm'], fill=self.COLOURS['white'])


    def build_game_not_started_image(self, game):
        """ Builds image for when the game has yet to start.
        Includes team logos and start time.

        Args:
            game (dict): Dictionary with all details of a specific game.
        """

        # First, add the team logos to the left and right images.
        self.add_team_logos_to_image(game)        

        # Add 'Today' to the centre image.
        self.draw['centre'].text((0, -1), 'T', font=self.FONTS['med'], fill=self.COLOURS['white']) # Text has some padding on the top that needs to be accounted for.
        self.draw['centre'].text((4, 1), 'o', font=self.FONTS['sm'], fill=self.COLOURS['white'])
        self.draw['centre'].text((8, 1), 'd', font=self.FONTS['sm'], fill=self.COLOURS['white'])
        self.draw['centre'].text((12, 1), 'a', font=self.FONTS['sm'], fill=self.COLOURS['white'])
        self.draw['centre'].text((16, 1), 'y', font=self.FONTS['sm'], fill=self.COLOURS['white'])

        # Add '@' to the centre image.
        self.draw['centre'].text((5, 7), '@', font=self.FONTS['lrg'], fill=self.COLOURS['white'])

        # Add the start time to the centre image.
        self.add_time_to_image(game)


    def build_game_in_progress_image(self, game):
        """ Builds image for when the game is in progress.
        Includes team logos, score, period, and time remaining.

        Args:
            game (dict): Dictionary with all details of a specific game.
        """

        # First, add the team logos to the left and right images.
        self.add_team_logos_to_image(game)

        # Add the period and time remaining to the centre image.
        self.add_playing_period_to_image(game) # This exists in child classes.
        if self.should_display_time_remaining_in_playing_period(game): # This exists in child classes.
            self.add_time_to_image(game)        

        # Add the current score to the centre image, noting if either team scored since previous data pull.
        self.add_score_to_image(game, overriding_team=game['scoring_team'], colour_override=self.COLOURS['red'])


    def build_game_complete_image(self, game):
        """ Builds image for when the game is complete.
        Include final score and if the game ended in OT, etc.

        Args:
            game (dict): Dictionary with all details of a specific game.
        """

        # First, add the team logos to the left and right images.
        self.add_team_logos_to_image(game)

        # Add 'Final' to the centre image.
        self.draw['centre'].text((0, -1), 'F', font=self.FONTS['med'], fill=self.COLOURS['white'])
        self.draw['centre'].text((4, 1), 'i', font=self.FONTS['sm'], fill=self.COLOURS['white'])
        self.draw['centre'].text((8, 1), 'n', font=self.FONTS['sm'], fill=self.COLOURS['white'])
        self.draw['centre'].text((13, 1), 'a', font=self.FONTS['sm'], fill=self.COLOURS['white'])
        self.draw['centre'].text((16, 1), 'l', font=self.FONTS['sm'], fill=self.COLOURS['white'])

        # If game ended in OT, etc. add that to the centre image.
        if game['league'] not in ['MLS']:
            self.add_final_playing_period_to_image(game) # This exists in child classes.

        # Add the current score to the centre image, noting if either team scored since previous data pull.
        self.add_score_to_image(game, overriding_team=game['scoring_team'], colour_override=self.COLOURS['red'])


    def add_time_to_image(self, game):
        """ Adds the start time or time remaining in the period to the centre image.

        Args:
            game (dict): Dictionary with all details of a specific game.
        """

        # First, get the time to be displayed as a sting, set a row offset if the game has yet to start.
        if game['has_started']:
            time_str = game['period_time_remaining']
            row_offset = 0
        else:
            time_str = game['start_datetime_local'].time().strftime('%I:%M')
            row_offset = 13 # Vertical offset if adding time remaining for an ongoing game vs start time of day for a game not started.

        # Add time to the centre image.
        
        if game['league'] in ['MLS']:
            if not game['has_started']:
                self.draw['centre'].text((0, 8 + row_offset), time_str[0], font=self.FONTS['sm'], fill=self.COLOURS['white'])
                self.draw['centre'].text((4, 8 + row_offset), time_str[1], font=self.FONTS['sm'], fill=self.COLOURS['white'])
                # Colon (manual dots since the font's colon looks funny).
                self.draw['centre'].point((9, 11 + row_offset), fill=self.COLOURS['white'])
                self.draw['centre'].point((9, 13 + row_offset), fill=self.COLOURS['white'])
                # Seconds.
                self.draw['centre'].text((11, 8 + row_offset), time_str[3], font=self.FONTS['sm'], fill=self.COLOURS['white']) # Skipping time_str[2] as that would be the colon.
                self.draw['centre'].text((15, 8 + row_offset), time_str[4], font=self.FONTS['sm'], fill=self.COLOURS['white'])
            elif '+' in time_str:
                self.draw['centre'].text((4, 7 + row_offset), time_str.split('+')[0], font=self.FONTS['sm'], fill=self.COLOURS['white'])
                self.draw['centre'].text((4, 13 + row_offset), ('+' + time_str.split('+')[1]), font=self.FONTS['sm'], fill=self.COLOURS['white'])
            else:
                self.draw['centre'].text((4, 9 + row_offset), time_str, font=self.FONTS['sm'], fill=self.COLOURS['white'])
            #self.draw['centre'].text((8, 8 + row_offset), time_str[1], font=self.FONTS['sm'], fill=self.COLOURS['white'])
            # Colon (manual dots since the font's colon looks funny).
            #self.draw['centre'].text((11, 8 + row_offset), "'", font=self.FONTS['sm'], fill=self.COLOURS['white'])

        elif time_str[0] == "2": # If the first digit of the time is 2. Will only occur when there's 20 mins left in a hockey period, never for a start time.
            # Minutes.
            self.draw['centre'].text((0, 8 + row_offset), time_str[0], font=self.FONTS['sm'], fill=self.COLOURS['white'])
            self.draw['centre'].text((4, 8 + row_offset), time_str[1], font=self.FONTS['sm'], fill=self.COLOURS['white'])
            # Colon (manual dots since the font's colon looks funny).
            self.draw['centre'].point((9, 11 + row_offset), fill=self.COLOURS['white'])
            self.draw['centre'].point((9, 13 + row_offset), fill=self.COLOURS['white'])
            # Seconds.
            self.draw['centre'].text((11, 8 + row_offset), time_str[3], font=self.FONTS['sm'], fill=self.COLOURS['white']) # Skipping time_str[2] as that would be the colon.
            self.draw['centre'].text((15, 8 + row_offset), time_str[4], font=self.FONTS['sm'], fill=self.COLOURS['white'])
            
        elif time_str[0] == "1": # If the first digit of the time is 1. When 10:00-19:59 left in per/qtr, or game start on or after 10pm.
            # Hours/minutes.
            self.draw['centre'].text((-1, 8 + row_offset), time_str[0], font=self.FONTS['sm'], fill=self.COLOURS['white']) # Need to acount for horizonal padding.
            self.draw['centre'].text((4, 8 + row_offset), time_str[1], font=self.FONTS['sm'], fill=self.COLOURS['white'])
            # Colon.
            self.draw['centre'].point((9, 11 + row_offset), fill=self.COLOURS['white'])
            self.draw['centre'].point((9, 13 + row_offset), fill=self.COLOURS['white'])
            # Minutes/seconds.
            self.draw['centre'].text((11, 8 + row_offset), time_str[3], font=self.FONTS['sm'], fill=self.COLOURS['white']) # Skipping time_str[2] as that would be the colon.
            self.draw['centre'].text((16, 8 + row_offset), time_str[4], font=self.FONTS['sm'], fill=self.COLOURS['white'])

        else: # If the first digit of the time is 0. When 0:00-9:59 left in per/qtr, or game start before 10pm.
            # Hour/minutes.
            self.draw['centre'].text((2, 8 + row_offset), time_str[1], font=self.FONTS['sm'], fill=self.COLOURS['white'])
            # Colon.
            self.draw['centre'].point((7, 11 + row_offset), fill=self.COLOURS['white'])
            self.draw['centre'].point((7, 13 + row_offset), fill=self.COLOURS['white'])
            # Minutes/seconds.
            self.draw['centre'].text((9, 8 + row_offset), time_str[3], font=self.FONTS['sm'], fill=self.COLOURS['white'])
            self.draw['centre'].text((14, 8 + row_offset), time_str[4], font=self.FONTS['sm'], fill=self.COLOURS['white'])


    def add_team_logos_to_image(self, game):
        """ Adds home and away team logos to the right and left images respectively. 
        Uses alt logos as specified in config.yaml.

        Args:
            game (dict): Dictionary with all details of a specific game.
        """
        
        # Determine the path of the image to load. Standard path or alt logo.
        away_logo_path = f'assets/images/{self.LEAGUE}/teams/{game['away_abrv']}.png' if game['away_abrv'] not in self.alt_logos else f'assets/images/{self.LEAGUE}/teams_alt/{game['away_abrv']}_{self.alt_logos[game['away_abrv']]}.png'
        
        # Load, crop, and resize the away team logo.
        away_logo = Image.open(away_logo_path)
        away_logo = image_utils.crop_image(away_logo)
        away_logo.thumbnail(self.images['left'].size)

        # Determine placement and add logo to the left image.
        away_placement_in_image = (
            self.images['left'].width - away_logo.width if away_logo.width > 21 else 19 + math.ceil((21 - away_logo.width) / 2), # Right align logo within the left image if logo is wider than image, otherwise centre.
            math.floor((self.images['left'].height - away_logo.height) / 2) # Middle align hight within left image (when logo is shorter than max image height). 
        )
        self.images['left'].paste(away_logo, away_placement_in_image)

        # Determine the path of the image to load. Standard path or alt logo.
        home_logo_path = f'assets/images/{self.LEAGUE}/teams/{game['home_abrv']}.png' if game['home_abrv'] not in self.alt_logos else f'assets/images/{self.LEAGUE}/teams_alt/{game['home_abrv']}_{self.alt_logos[game['home_abrv']]}.png'

        # Load, crop, and resize the home team logo.
        home_logo = Image.open(home_logo_path)
        home_logo = image_utils.crop_image(home_logo)
        home_logo.thumbnail(self.images['right'].size)

        # Determine placement and add logo to the right image.
        home_placement_in_image = (
            0 if home_logo.width > 21 else math.floor((21 - home_logo.width) / 2), # Left align logo within the right image if logo is wider than image, otherwise centre.
            math.floor((self.images['right'].height - home_logo.height) / 2) # Middle align hight within right image (when logo is shorter than max image height). 
        )
        self.images['right'].paste(home_logo, home_placement_in_image)


    def add_score_to_image(self, game, overriding_team=None, colour_override=None):
        """ Adds home and away team scores to the centre image.
        Score can appear in a custom colour by specifying an overriding_team and colour_override. These are configurable by the user in config.yaml.

        Args:
            game (dict): Dictionary with all details of a specific game.
            overriding_team (str): Which team should have their colour overridden. 'home', 'away', 'both', or None. Defaults to None.
            colour_override (tuple): Colour that the overriding_team's score should appear in. Defaults to None.
        """

        # First, default both team's score colour to white.
        colour_away = self.COLOURS['white']
        colour_home = self.COLOURS['white']

        # Check one or both teams scored. Set the team's starting colour to colour_override if that team scored.
        if self.settings['score_alerting']['score_coloured']:
            colour_away = colour_override if overriding_team in ['away', 'both'] else colour_away
            colour_home = colour_override if overriding_team in ['home', 'both'] else colour_home

        # Note the number of digits in the scores.
        away_score_digits = len(str(game['away_score']))
        home_score_digits = len(str(game['home_score']))
        
        # If both scores are <10, display large numbers and a hyphen in set locations.
        if max(away_score_digits, home_score_digits) == 1:
            # Add the hyphen to the centre image.
            self.draw['centre'].text((8, 19), "-", font=self.FONTS['sm_bold'], fill=self.COLOURS['white'])

            # Add the scores to the centre image with the colour determined above.
            self.draw['centre'].text((0, 16), str(game['away_score']), font=self.FONTS['lrg_bold'], fill=colour_away)
            self.draw['centre'].text((12, 16), str(game['home_score']), font=self.FONTS['lrg_bold'], fill=colour_home)

        # Otherwise, smaller numbers and no hyphen.
        else:
            # Determine the larger score. Use to determine vertical placement, putting the higher score higher up.
            if game['away_score'] >= game['home_score']:
                away_team_row_start = 17
                home_team_row_start = 23
            else:
                away_team_row_start = 23
                home_team_row_start = 17

            # Add away score to centre image.
            away_score_col_start = -1 if str(game['away_score'])[0] == '1' else 0
            self.draw['centre'].text((away_score_col_start, away_team_row_start), str(game['away_score']), font=self.FONTS['sm'], fill=colour_away)

            # Dynamically determin placement of home team score based on number of digits. Add to centre image.
            home_score_col_start = 20 - (5 * home_score_digits - 1)
            self.draw['centre'].text((home_score_col_start, home_team_row_start), str(game['home_score']), font=self.FONTS['sm'], fill=colour_home)


    def add_league_logo_to_image(self):
        """ Adds logo for a specific league to the full image.
        League is determined in the extended class specific to each league.
        """

        # Load, crop, and resize the league logo.
        league_logo = Image.open(f'assets/images/{self.LEAGUE}/league/{self.LEAGUE}.png')
        league_logo = image_utils.crop_image(league_logo)
        league_logo.thumbnail((30, 30))

        # Determine placement, centre within the left half of the matrix.
        row_location = math.floor(1 + (30 - league_logo.size[0]) / 2)
        col_location = math.ceil(1 + (30 - league_logo.size[1]) / 2)

        # Add it to the centre image.
        self.images['full'].paste(league_logo, (row_location, col_location))


    def fade_score_change(self, game):
        """ Fades score from red to white after a goal is scored.
        Achieved by rapidly calculating a new colour and re-adding the score to the centre image before displaying again.

        Args:
            game (dict): Dictionary with all details of a specific game.
        """

        # Stay red for a short time before fading.
        sleep(0.5)

        # Loop over the colour between red and white.
        for n in range(self.COLOURS['red'][2], self.COLOURS['white'][2]):
            # Add score to the centre image, with the new colour.
            self.add_score_to_image(game, overriding_team=game['scoring_team'], colour_override=(255, n, n))
            
            # Rebuild the full image and display on matrix.
            self.images['full'].paste(self.images['left'], (-19, 1))
            self.images['full'].paste(self.images['centre'], (22, 1))
            self.images['full'].paste(self.images['right'], (43, 1))
            matrix.SetImage(self.images['full'])
            sleep(0.015) # Sleep for a short time to pace animation.


    def transition_image(self, direction, image_already_combined=False):
        """ Transitions between image and blank screen or vise versa.
        Practically, this means the transition between games (one direction). Transition is set in config.yaml.

        Args:
            direction (str): Direction of the transition. 'in' or 'out'.
            image_already_combined (bool, optional): If the image was build directly to the full image. If true, skip building it here. Defaults to False.
        """

        # 'Cut' transition.
        if self.settings['transition'] == 'cut':
            if direction == 'in':
                # Build combined image if needed.
                if not image_already_combined:
                    self.images['full'].paste(self.images['left'], (-19, 1))
                    self.images['full'].paste(self.images['centre'], (22, 1))
                    self.images['full'].paste(self.images['right'], (43, 1))
                
                # Since there's no animation of any sort, an out transition is not needed. Simply display the image on the matrix.
                matrix.SetImage(self.images['full'])
        
        # 'Fade' transition.
        elif self.settings['transition'] == 'fade':
            # Define the 'fade rule', that is the steps between 0 (transparent) and 255 (opaque).
            fade = (255, -1, -15) if direction == 'in' else (0, 256, 15)

            # Build combined image if needed.
            if not image_already_combined:
                self.images['full'].paste(self.images['left'], (-19, 1))
                self.images['full'].paste(self.images['centre'], (22, 1))
                self.images['full'].paste(self.images['right'], (43, 1))

            # Loop over opacities to apply to image.
            for overlay_opacity in range(*fade):
                # Create faded image to display on matrix.
                faded_for_display_image = self.create_faded_image(self.images['full'], overlay_opacity)

                # Display and sleep for a short time to pace the animation.
                matrix.SetImage(faded_for_display_image)
                sleep(0.025)

            # Hold a moment with nothing displayed after fading out.
            if direction == 'out':
                sleep(0.2)

        # 'Modern' transition.
        elif self.settings['transition'] == 'modern':
            # Define the 'fade rule', that is the steps between 0 (transparent) and 255 (opaque).
            fade = (255, -1, -15) if direction == 'in' else (0, 256, 15)

            # If the final image already exists, make a copy for later use.
            if image_already_combined:
                combined_image = self.images['full'].copy()

            if direction == 'in':
                # Loop over opacities to apply to image and horizontal movement via col_offset.
                for overlay_opacity, col_offset in zip(range(*fade), range(-len(range(*fade))+1, 1, 1)):
                    # Rebuild full image with offsets. Will first need to clear the image. This will also ensure there's no artifacts between loops of animation.    
                    image_utils.clear_image(self.images['full'], self.draw['full'])
                    
                    # If the image has not already been combined, add each sub-image to the full with a col_offset applied.
                    if not image_already_combined:                        
                        self.images['full'].paste(self.images['left'], (-19 + col_offset, 1))
                        self.images['full'].paste(self.images['centre'], (22 + col_offset, 1))
                        self.images['full'].paste(self.images['right'], (43 + col_offset, 1))          
                    # Otherwise, copy the combined_image copied above to full with a col_offset applied.
                    else:
                        self.images['full'].paste(combined_image, (col_offset, 0))

                    # Create faded image to display on matrix.
                    faded_for_display_image = self.create_faded_image(self.images['full'], overlay_opacity)

                    # Display and sleep for a short time to pace the animation.
                    matrix.SetImage(faded_for_display_image)
                    sleep(0.025)
            
            elif direction == 'out':
                # Loop over opacities to apply to image and horizontal movement via col_offset.
                for overlay_opacity, col_offset in zip(range(*fade), range(0, len(range(*fade)), 1)):
                    # Rebuild full image with offsets. Will first need to clear the image. This will also ensure there's no artifacts between loops of animation.    
                    image_utils.clear_image(self.images['full'], self.draw['full'])
                    
                    # If the image has not already been combined, add each sub-image to the full with a col_offset applied.
                    if not image_already_combined:                        
                        self.images['full'].paste(self.images['left'], (-19 + col_offset, 1))
                        self.images['full'].paste(self.images['centre'], (22 + col_offset, 1))
                        self.images['full'].paste(self.images['right'], (43 + col_offset, 1))       
                    # Otherwise, copy the combined_image copied above to full with a col_offset applied.
                    else:
                        self.images['full'].paste(combined_image, (col_offset, 0))

                    # Create faded image to display on matrix.
                    faded_for_display_image = self.create_faded_image(self.images['full'], overlay_opacity)

                    # Display and sleep for a short time to pace the animation.
                    matrix.SetImage(faded_for_display_image)
                    sleep(0.025)

                # Hold a moment with nothing displayed.
                sleep(0.2)

        # On way out of 'out' transitions, reset all images to black for next image build.
        if direction == 'out':
            for image, image_draw in zip(self.images.values(), self.draw.values()):
                image_utils.clear_image(image, image_draw)