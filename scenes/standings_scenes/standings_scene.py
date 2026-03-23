from ..scene import Scene
from setup.matrix_setup import matrix, matrix_options
from utils import image_utils

from PIL import Image, ImageDraw
from time import sleep
import math


class StandingsScene(Scene):
    """ Generic scene for standings, regardless of league/sport. Contains functionality to build images and display them on the matrix.
    This class extends the general Scene class and is extended by those of specific leagues. An object of this class type is never created directly.
    """
    
    def __init__(self):
        """ Creates Image objects to be displayed on the matrix and ImageDraw objects allowing us to add logos, text, etc. to the images.
        First runs init from generic Scene class.
        """

        super().__init__()

        # Image objects.
        self.images = {
            'side':             Image.new('RGB', (8, matrix_options.rows)),
            'standings_rows':   [], # Represents the individual rows in the standings, will be populated later.
            'standings':        Image.new('RGB', (56, 256)),
            'full':             Image.new('RGB', (matrix_options.cols, matrix_options.rows)),

        }

        # ImageDraw object associated with each of the above Image objects.
        self.draw = {
            'side':             ImageDraw.Draw(self.images['side']),
            'standings_rows':   [],
            'standings':        ImageDraw.Draw(self.images['standings']),
            'full':             ImageDraw.Draw(self.images['full'])
        }


    def build_splash_image(self, date):
        """ Builds splash screen image.
        Includes league logo and date.

        Args:
            num_games (int): Number of games on the provided date.
            date (date): Date to display.
        """

        # First, add the league logo image.
        self.add_league_logo_to_image()

        # Add 'Stand' and a horizontal line.
        self.draw['full'].text((33, 0), 'Stand', font=self.FONTS['med_bold'], fill=self.COLOURS['white'])
        self.draw['full'].line([(32, 10), (62, 10)], fill=self.COLOURS['white'])

        # Note the month (3 char) and day number.
        month = date.strftime('%b')
        day = date.strftime('%-d')

        # Determine horizontal location, and add the date.
        month_col = 37 if len(day) == 1 else 35
        self.draw['full'].text((month_col, 12), month, font=self.FONTS['sm'], fill=self.COLOURS['white'])
        day_col = 53 if len(day) == 1 else 51
        self.draw['full'].text((day_col, 12), day, font=self.FONTS['sm'], fill=self.COLOURS['white'])


    # def build_standings_image(self, standing, rank_method, standing_type, standing_type_extended=None, playoff_cutoff_hard=0, playoff_cutoff_soft=0, relegation_cutoff=0):
    def build_standings_image(self, standing_details):
        """ Build overall standings image. Includes standing type in sidebar, and the actual standings by team.

        Args:
            standing_details (dict): Dict containing all details needed to build the standings image. Expected to contain at least a 'team_standings' key with a list of dicts with standings, and a 'rank_method' key with the method used to rank teams (e.g. 'Points', 'Win Percentage', etc.).
                                     May also contain keys for 'playoff_cutoff_hard', 'playoff_cutoff_soft', and 'relegation_cutoff' to determine where to place coloured lines in the standings.
        """

        # For the sideways text in the sidebar, create a temp image, then rotate that.
        tmp_img = Image.new('RGB', self.images['side'].size[::-1])
        tmp_draw = ImageDraw.Draw(tmp_img)
        
        # First, add the background and text to the non-rotated image.
        tmp_draw.rectangle([(0, 0), (31, 7)], fill=self.COLOURS['white'])
        tmp_draw.text((1, 0), self.LEAGUE, font=self.FONTS['sm'], fill=self.COLOURS['black'])

        # If standing subdivision ('EC', 'ALE', etc.) provided, determine the correct location based on length and add those as well.
        # If nothing provided, will just display the league name.
        if standing_details.get('subdivision_abrv'):
            sub_len = len(standing_details['subdivision_abrv'])
            sub_col = 32 - 5 * sub_len
            tmp_draw.text((sub_col, 0), standing_details['subdivision_abrv'], font=self.FONTS['sm'], fill=self.COLOURS['black'])

        # If enabled in config.yaml, add a highlight colour to the sidebar. Helps differentiate between different leagues.
        if self.settings.get('colour_sidebar'):
            tmp_draw.line([(0, 0), (31, 0)], fill=self.COLOURS['sidebar_highlight'])
        
        # Then rotate and paste onto the side image.
        tmp_img = tmp_img.rotate(90, expand=True)
        self.images['side'].paste(tmp_img, (0,0))

        # Build the individual standing row images and overall standing image.
        self.build_standing_row_images(standing_details)


    # def build_standing_row_images(self, standings, rank_method, playoff_cutoff_hard=0, playoff_cutoff_soft=0, relegation_cutoff=0):
    def build_standing_row_images(self, standing_details):
        """ Builds images for each standing row (each team + details), as well as one for all the standings.

        Args:
            standing_details (dict): Dict containing all details needed to build the standings image. Expected to contain at least a 'team_standings' key with a list of dicts with standings, and a 'rank_method' key with the method used to rank teams (e.g. 'Points', 'Win Percentage', etc.).
                                     May also contain keys for 'playoff_cutoff_hard', 'playoff_cutoff_soft', and 'relegation_cutoff' to determine where to place coloured lines in the standings.
        """

        # Reset standing rows back to an empty list and note the number of teams to display.
        self.images['standings_rows'] = []
        num_teams = len(standing_details['team_standings'])

        # For each team in the standings, build an image with just that row, append to a list, and add to the overall standings image.
        for row, team in enumerate(standing_details['team_standings']):
            # Create temp Image and ImageDraw objects for the row.
            tmp_img = Image.new('RGB', (self.images['standings'].size[0], 8))
            tmp_draw = ImageDraw.Draw(tmp_img)

            # Determine the horizontal line colour based on the provided playoff/relegation cutoff(s).
            if row == standing_details.get('playoff_cutoff_hard', 0) - 1:
                line_colour = self.COLOURS['red']
            elif row == standing_details.get('playoff_cutoff_soft', 0) - 1:
                line_colour = self.COLOURS['green']
            elif row == standing_details.get('relegation_cutoff', 0) - 1:
                line_colour = self.COLOURS['red']
            else:
                line_colour = self.COLOURS['grey_dark']
            
            # Add a horizontal line to the image. Skip this in the final iteration.
            if row != num_teams-1:
                tmp_draw.line([(1, 7), (54, 7)], fill=line_colour)
            
            # Determine the colour for each row's text based on if the team is a favourite per config.yaml.
            team_colour = self.COLOURS['white'] # Default white.
            if self.favourite_teams and self.settings['highlight_fav_teams']:
                if team['team_abrv'] in self.favourite_teams:
                    team_colour = self.COLOURS['yellow'] # Favs are yellow.

            # Determine placement of team ranking and add to image.
            rank_offset = 5 if len(str(team['rank'])) < 2 else 0
            tmp_draw.text((1+rank_offset, -1), str(team['rank']), font=self.FONTS['sm'], fill=team_colour)

            # Add a red star if the team has clinched a playoff spot.
            if team['has_clinched']:
                tmp_draw.text((14, -2), '*', font=self.FONTS['med'], fill=self.COLOURS['red'])

            # TODO: Add a gold star if the team has clinched the league title. Applicable for non-playoff sports only.
            
            # Add team abrv.
            tmp_draw.text((21, -1), team['team_abrv'], font=self.FONTS['sm'], fill=team_colour)

            if standing_details['rank_method'] in ['Points', 'Wins']:
                # Determine placement offset of team points based on length.
                ranker_to_display = str(team['points'])
                ranker_len = len(ranker_to_display)
                ranker_offset = -5 * (ranker_len - 1)

            elif standing_details['rank_method'] == 'Win Percentage':
                # Determine placement offset of win percentage based on length.
                ranker_to_display = team['percent'][2:] if team['percent'].startswith('0') else '00' # Looks odd, but will help display as 1.00.
                
                # If win percentage is 1.00, we'll manually add the '1.' now and '00' below.
                if ranker_to_display == '00':
                    ranker_offset = -5
                    tmp_draw.point((51+ranker_offset-2, 5), fill=team_colour)
                    tmp_draw.text((51+ranker_offset-7, -1), '1', font=self.FONTS['sm'], fill=team_colour)
                # Otherwise, set the offset and add a decimal point.
                else:
                    ranker_offset = -10
                    tmp_draw.point((51+ranker_offset-2, 5), fill=team_colour)
            
            elif standing_details['rank_method'] == 'Games Back':
                pass # TODO: implement in future.

            # Add ranker to image.
            tmp_draw.text((51+ranker_offset, -1), ranker_to_display, font=self.FONTS['sm'], fill=team_colour)

            # Append the temp image to standings_rows.
            self.images['standings_rows'].append(tmp_img)
            
            # Lastly, add to the overall standings image as well.
            offset = row * 8
            self.images['standings'].paste(tmp_img, (0, offset))    


    def scroll_standings_image(self):
        """ Scrolls the overall standing image down on the matrix, pausing after each complete row.
        """

        # Determine how many rows may need to be scrolled over.
        num_teams = len(self.images['standings_rows'])
        row_delta = -8 * max(num_teams - 4, 0) # If there's 4 or fewer teams to display, there will be no scrolling need.

        # Loop over the distance, updating the full image w/ a new location for the standings image.
        for offset in range(0, row_delta - 1, -1):
            # Clear the main image and rebuild with new placements.
            image_utils.clear_image(self.images['full'], self.draw['full'])
            self.images['full'].paste(self.images['side'], (0, 0))
            self.images['full'].paste(self.images['standings'], (8 , offset))

            # Display and hold for a duration specified in config.yaml. This is the very short time between frames.
            matrix.SetImage(self.images['full'])
            sleep(self.settings['scroll']['scroll_frame_duration'])

            # If scrolled a full row, pause longer as specified in config.yaml.
            if offset % 8 == 0:
                sleep(self.settings['scroll']['scroll_pause_duration'])


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


    def transition_image(self, direction, image_already_combined=False):
        """ Transitions between image and blank screen or vise versa.
        Practically, this means the transition between standing sets. Transition is set in config.yaml.

        Args:
            direction (str): Direction of the transition. 'in' or 'out'.
            image_already_combined (bool, optional): If the image was build directly to the full image. If true, skip building it here. Defaults to False.
        """

        # 'Cut' transition.
        if self.settings['transition'] == 'cut':
            if direction == 'in':
                # Build combined image if needed.
                if not image_already_combined:
                    self.images['full'].paste(self.images['side'], (0, 0))
                    self.images['full'].paste(self.images['standings'], (8, 0))
                
                # Since there's no animation of any sort, an out transition is not needed. Simply display the image on the matrix.
                matrix.SetImage(self.images['full'])
        
        # 'Fade' transition.
        elif self.settings['transition'] == 'fade':
            # Define the 'fade rule', that is the steps between 0 (transparent) and 255 (opaque).
            fade = (255, -1, -15) if direction == 'in' else (0, 256, 15)

            # Build combined image if needed, don't need to do on the way out as the image is already build from the scroll.
            if not image_already_combined and direction == 'in':
                self.images['full'].paste(self.images['side'], (0, 0))
                self.images['full'].paste(self.images['standings'], (8, 0))

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
                        self.images['full'].paste(self.images['side'], (0 + col_offset, 0))
                        self.images['full'].paste(self.images['standings'], (8 + col_offset, 0))   
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
                        # Determine the vertical offset needed to account for any scrolling that occurred.
                        row_offset = -8 * max(len(self.images['standings_rows']) - 4, 0)           
                        self.images['full'].paste(self.images['side'], (0 + col_offset, 0))
                        self.images['full'].paste(self.images['standings'], (8 + col_offset, row_offset))      
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