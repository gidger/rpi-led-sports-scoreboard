from ..scene import Scene
from setup.matrix_setup import matrix, matrix_options
from utils import image_utils
from data.soccer_data import get_team_logo

from PIL import Image, ImageDraw
from time import sleep
from pathlib import Path
import math


class FavTeamNextGameScene(Scene):
    """ Generic scene for favourite teams next games, regardless of league/sport. Contains functionality to build images and display them on the matrix.
    This class extends the general Scene class and is extended by those of specific leagues. An object of this class type is never created directly.
    """
    
    def __init__(self):
        """ Creates Image object to be displayed on the matrix and ImageDraw object allowing us to add logos, text, etc. to the image.
        First runs init from generic Scene class.
        """

        super().__init__()

        # Image object.
        self.images = {
            'full':     Image.new('RGB', (matrix_options.cols, matrix_options.rows))
        }

        # ImageDraw object ssociated with each of the above Image objects.
        self.draw = {
            'full':     ImageDraw.Draw(self.images['full'])
        }


    def build_next_game_image(self, team, game):
        """ Builds next game image for the specified team and game.

        Args:
            team (str): Three char team abrv to build next game image for.
            game (dit): Dict of next game details.
        """

        # First, add the team logo to the image.
        self.add_team_logo_to_image(team)

        # Add 'Next' and a horizontal line.
        self.draw['full'].text((36, 0), 'Next', font=self.FONTS['med_bold'], fill=self.COLOURS['white'])
        self.draw['full'].line([(34, 10), (60, 10)], fill=self.COLOURS['white'])

        # If the next game is today.
        if game['is_today']:
            # If the game has started, display 'IPR'.
            if game['has_started']:
                self.draw['full'].text((38, 11), 'IPR', font=self.FONTS['med'], fill=self.COLOURS['white'])
            # Otherwise, add start time of today's game.
            else:
                time_str = game['start_datetime_local'].time().strftime('%I:%M')
                if time_str[0] == "1": # If the first digit of the time is 1. When 10:00-19:59 left in per/qtr, or game start on or after 10pm.
                    # Hour/minutes.
                    self.draw['full'].text((35, 11), time_str[0], font=self.FONTS['med'], fill=self.COLOURS['white']) # Need to acount for horizonal padding.
                    self.draw['full'].text((41, 11), time_str[1], font=self.FONTS['med'], fill=self.COLOURS['white'])
                    # Colon.
                    self.draw['full'].point((47, 15), fill=self.COLOURS['white'])
                    self.draw['full'].point((47, 17), fill=self.COLOURS['white'])
                    # Minutes/seconds.
                    self.draw['full'].text((49, 11), time_str[3], font=self.FONTS['med'], fill=self.COLOURS['white'])
                    self.draw['full'].text((55, 11), time_str[4], font=self.FONTS['med'], fill=self.COLOURS['white'])

                else: # If the first digit of the time is 0. When 0:00-9:59 left in per/qtr, or game start before 10pm.
                    # Hour/minutes.
                    self.draw['full'].text((38, 11), time_str[1], font=self.FONTS['med'], fill=self.COLOURS['white'])
                    # Colon.
                    self.draw['full'].point((44, 15), fill=self.COLOURS['white'])
                    self.draw['full'].point((44, 17), fill=self.COLOURS['white'])
                    # Minutes/seconds.
                    self.draw['full'].text((46, 11), time_str[3], font=self.FONTS['med'], fill=self.COLOURS['white'])
                    self.draw['full'].text((52, 11), time_str[4], font=self.FONTS['med'], fill=self.COLOURS['white'])
        # If the game is not today add the game date to the image.
        else:
            # Note the month (3 char) and day number.
            month = game['start_datetime_local'].strftime('%b')
            day = game['start_datetime_local'].strftime('%-d')

            # Determine horizontal location, and add the date.
            month_col = 37 if len(day) == 1 else 35
            self.draw['full'].text((month_col, 12), month, font=self.FONTS['sm'], fill=self.COLOURS['white'])
            day_col = 53 if len(day) == 1 else 51
            self.draw['full'].text((day_col, 12), day, font=self.FONTS['sm'], fill=self.COLOURS['white'])

        # Add 'VS'/'@' and the opposing team name to the image.
        if game['home_or_away'] == 'home':
            self.draw['full'].text((34, 23), 'V', font=self.FONTS['sm'], fill=self.COLOURS['white'])
            self.draw['full'].text((38, 23), 'S', font=self.FONTS['sm'], fill=self.COLOURS['white'])
            self.draw['full'].text((44, 21), game['opponent_abrv'], font=self.FONTS['med_bold'], fill=self.COLOURS['white'])
        else:
            self.draw['full'].text((35, 21), '@', font=self.FONTS['med'], fill=self.COLOURS['white'])
            self.draw['full'].text((43, 21), game['opponent_abrv'], font=self.FONTS['med_bold'], fill=self.COLOURS['white'])


    def add_team_logo_to_image(self, team):
        """ Adds logo for a specific team to the full image. Uses alt logo if specified in config.yaml.
        League is determined in the extended class specific to each league.
        """

        # Determine the path of the image to load. Standard path or alt logo.
        logo_path = f'assets/images/{self.LEAGUE}/teams/{team}.png' if team not in self.alt_logos else f'assets/images/{self.LEAGUE}/teams_alt/{team}_{self.alt_logos[team]}.png'

        if not Path(logo_path).exists():
            get_team_logo(team, self)
            image_utils.process_in_place(logo_path)

        # Load, crop, and resize the team logo.
        team_logo = Image.open(logo_path)
        team_logo = image_utils.crop_image(team_logo)
        team_logo.thumbnail((30, 30))

        # Determine placement, centre within the left half of the matrix.
        row_location = math.floor(1 + (30 - team_logo.size[0]) / 2)
        col_location = math.ceil(1 + (30 - team_logo.size[1]) / 2)

        # Add it to the image.
        self.images['full'].paste(team_logo, (row_location, col_location))


    def transition_image(self, direction):
        """ Transitions between image and blank screen or vise versa.
        Transition is set in config.yaml.

        Args:
            direction (str): Direction of the transition. 'in' or 'out'.
        """

        # 'Cut' transition.
        if self.settings['transition'] == 'cut':
            if direction == 'in':                
                # Since there's no animation of any sort, an out transition is not needed. Simply display the image on the matrix.
                matrix.SetImage(self.images['full'])
        
        # 'Fade' transition.
        elif self.settings['transition'] == 'fade':
            # Define the 'fade rule', that is the steps between 0 (transparent) and 255 (opaque).
            fade = (255, -1, -15) if direction == 'in' else (0, 256, 15)

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

            # Make a copy of the image for later use.
            combined_image = self.images['full'].copy()

            if direction == 'in':
                # Loop over opacities to apply to image and horizontal movement via col_offset.
                for overlay_opacity, col_offset in zip(range(*fade), range(-len(range(*fade))+1, 1, 1)):
                    # Rebuild full image with offsets. Will first need to clear the image. This will also ensure there's no artifacts between loops of animation.    
                    image_utils.clear_image(self.images['full'], self.draw['full'])
                           
                    # Copy the combined_image copied above to full with a col_offset applied.
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
                         
                    # Copy the combined_image copied above to full with a col_offset applied.
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