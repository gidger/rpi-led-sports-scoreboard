from ..scene import Scene
from setup.matrix_setup import matrix, matrix_options
from utils.f1_api import get_driver_standings
from utils.data_utils import read_yaml
from PIL import Image, ImageDraw
import time


# Points gap that triggers the "clinched" indicator (cosmetic only, not computed here)
_CLINCH_THRESHOLD = 9999


class F1DriverStandingsScene(Scene):
    """
    Scrolling WDC standings display.

    Each driver occupies one full screen (64×32):
        Red header bar  "WDC STANDINGS"
        P1  HAM  McLaren
              256 PTS

    The list scrolls through all fetched drivers (default top 10),
    pausing briefly on each entry before sliding to the next.

    Reads settings from config.yaml under scene_settings.f1.driver_standings.
    """

    def __init__(self):
        super().__init__()
        self.image      = Image.new('RGB', (matrix_options.cols, matrix_options.rows))
        self.draw       = ImageDraw.Draw(self.image)
        self.fav_drivers = []

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def display_scene(self):
        cfg      = read_yaml('config.yaml')
        settings = cfg['scene_settings']['f1']['driver_standings']
        self.fav_drivers = [d.upper() for d in cfg.get('favourite_drivers', [])]

        highlight = settings.get('highlight_fav_drivers', True)
        frame_dur = settings.get('scroll', {}).get('scroll_frame_duration', 0.075)
        pause_dur = settings.get('scroll', {}).get('scroll_pause_duration', 1.0)

        # Splash
        if settings.get('splash', {}).get('display_splash', True):
            self._show_splash(settings['splash'].get('splash_display_duration', 2))

        standings = get_driver_standings(limit=10)
        if not standings:
            return

        self._scroll_standings(standings, highlight, frame_dur, pause_dur)

    # ------------------------------------------------------------------
    # Splash
    # ------------------------------------------------------------------

    def _show_splash(self, duration):
        splash = Image.new('RGB', (matrix_options.cols, matrix_options.rows), self.COLOURS['black'])
        draw   = ImageDraw.Draw(splash)

        try:
            logo = Image.open('assets/images/f1/league/f1.png').convert('RGBA')
            logo = logo.resize((32, 14), Image.Resampling.LANCZOS)
            splash.paste(logo, (16, 3), logo)
        except Exception:
            draw.text((22, 4), 'F1', font=self.FONTS['lrg_bold'], fill=self.COLOURS['red'])

        label   = 'DRIVERS'
        label_x = (matrix_options.cols - len(label) * 5) // 2
        draw.text((label_x, 20), label, font=self.FONTS['sm'], fill=self.COLOURS['yellow'])
        matrix.SetImage(splash)
        time.sleep(duration)

    # ------------------------------------------------------------------
    # Scrolling renderer
    # ------------------------------------------------------------------

    def _scroll_standings(self, standings, highlight, frame_dur, pause_dur):
        """
        Renders a tall strip (len * 32 pixels) then scrolls it upward,
        pausing for pause_dur seconds each time a new entry is centred.
        """
        count       = len(standings)
        strip_h     = count * matrix_options.rows          # total pixel height
        strip_img   = Image.new('RGB', (matrix_options.cols, strip_h))
        strip_draw  = ImageDraw.Draw(strip_img)

        for idx, driver in enumerate(standings):
            y_off = idx * matrix_options.rows
            self._draw_driver_card(strip_draw, strip_img, driver, y_off, highlight)

        # Scroll through the strip
        for y in range(0, strip_h - matrix_options.rows + 1):
            frame = strip_img.crop((0, y, matrix_options.cols, y + matrix_options.rows))
            matrix.SetImage(frame)

            # Pause when a card snaps into full view
            if y % matrix_options.rows == 0:
                time.sleep(pause_dur)
            else:
                time.sleep(frame_dur)

    # ------------------------------------------------------------------
    # Card drawing
    # ------------------------------------------------------------------

    def _draw_driver_card(self, draw, strip_img, driver, y_off, highlight):
        """
        Draws one driver entry onto the strip at vertical offset y_off.

        Layout (each card is 64×32):
          Row 0–7   Red header  "WDC STANDINGS"
          Row 9–16  Pos + Code  (yellow if favourite)
          Row 18–25 Constructor short name (grey)
          Row 25–31 Points (white) + wins badge if applicable
        """
        rows = matrix_options.rows
        cols = matrix_options.cols

        # Background
        draw.rectangle([(0, y_off), (cols, y_off + rows)], fill=self.COLOURS['black'])

        # Header bar
        draw.rectangle([(0, y_off), (cols, y_off + 7)], fill=self.COLOURS['red'])
        draw.text((2, y_off), 'WDC STANDINGS', font=self.FONTS['sm_bold'], fill=self.COLOURS['white'])

        # Position
        pos_colour = self._pos_colour(driver['pos'])
        draw.text((2, y_off + 9), f"P{driver['pos']}", font=self.FONTS['sm_bold'], fill=pos_colour)

        # Driver code
        code        = driver['code']
        code_colour = (self.COLOURS['yellow']
                       if highlight and code in self.fav_drivers
                       else self.COLOURS['white'])
        draw.text((22, y_off + 9), code, font=self.FONTS['sm_bold'], fill=code_colour)

        # Wins badge (only if driver has at least one win)
        if driver.get('wins', 0) > 0:
            win_text = f"{driver['wins']}W"
            draw.text((48, y_off + 9), win_text, font=self.FONTS['sm'], fill=self.COLOURS['green'])

        # Constructor
        from utils.f1_api import _CONSTRUCTOR_NAMES
        cid       = driver.get('constructor_id', '')
        team_name = _CONSTRUCTOR_NAMES.get(cid, cid[:8].upper())
        draw.text((2, y_off + 18), team_name, font=self.FONTS['sm'], fill=self.COLOURS['grey_light'])

        # Points
        pts_text = f"{driver['points']} PTS"
        draw.text((2, y_off + 25), pts_text, font=self.FONTS['sm'], fill=self.COLOURS['white'])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pos_colour(pos):
        if pos == 1:
            return (255, 209, 0)
        if pos == 2:
            return (180, 180, 180)
        if pos == 3:
            return (180, 100, 40)
        return (255, 255, 255)
