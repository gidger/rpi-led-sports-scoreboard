from ..scene import Scene
from setup.matrix_setup import matrix, matrix_options
from utils.f1_api import get_constructor_standings
from utils.data_utils import read_yaml
from PIL import Image, ImageDraw
import time


class F1ConstructorStandingsScene(Scene):
    """
    Scrolling WCC (constructor championship) standings display.

    Each constructor occupies one full screen (64×32):
        Red header bar  "WCC STANDINGS"
        P1  MCLAREN
              312 PTS  (3W)

    Reads settings from config.yaml under scene_settings.f1.constructor_standings.
    """

    def __init__(self):
        super().__init__()
        self.image = Image.new('RGB', (matrix_options.cols, matrix_options.rows))
        self.draw  = ImageDraw.Draw(self.image)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def display_scene(self):
        cfg      = read_yaml('config.yaml')
        settings = cfg['scene_settings']['f1']['constructor_standings']

        frame_dur = settings.get('scroll', {}).get('scroll_frame_duration', 0.075)
        pause_dur = settings.get('scroll', {}).get('scroll_pause_duration', 1.0)

        # Splash
        if settings.get('splash', {}).get('display_splash', True):
            self._show_splash(settings['splash'].get('splash_display_duration', 2))

        standings = get_constructor_standings(limit=10)
        if not standings:
            return

        self._scroll_standings(standings, frame_dur, pause_dur)

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

        label   = 'CONSTRUCTORS'
        label_x = max(0, (matrix_options.cols - len(label) * 5) // 2)
        draw.text((label_x, 20), label, font=self.FONTS['sm'], fill=self.COLOURS['yellow'])
        matrix.SetImage(splash)
        time.sleep(duration)

    # ------------------------------------------------------------------
    # Scrolling renderer
    # ------------------------------------------------------------------

    def _scroll_standings(self, standings, frame_dur, pause_dur):
        count    = len(standings)
        strip_h  = count * matrix_options.rows
        strip    = Image.new('RGB', (matrix_options.cols, strip_h))
        s_draw   = ImageDraw.Draw(strip)

        for idx, team in enumerate(standings):
            y_off = idx * matrix_options.rows
            self._draw_team_card(s_draw, team, y_off)

        for y in range(0, strip_h - matrix_options.rows + 1):
            frame = strip.crop((0, y, matrix_options.cols, y + matrix_options.rows))
            matrix.SetImage(frame)
            if y % matrix_options.rows == 0:
                time.sleep(pause_dur)
            else:
                time.sleep(frame_dur)

    # ------------------------------------------------------------------
    # Card drawing
    # ------------------------------------------------------------------

    def _draw_team_card(self, draw, team, y_off):
        """
        Layout (64×32 per card):
          Row 0–7   Red header  "WCC STANDINGS"
          Row 9–16  Pos  +  Short team name
          Row 18–25 Full name (smaller, grey)
          Row 25–31 Points  + wins
        """
        rows = matrix_options.rows
        cols = matrix_options.cols

        draw.rectangle([(0, y_off), (cols, y_off + rows)], fill=self.COLOURS['black'])

        # Header
        draw.rectangle([(0, y_off), (cols, y_off + 7)], fill=self.COLOURS['red'])
        draw.text((2, y_off), 'WCC STANDINGS', font=self.FONTS['sm_bold'], fill=self.COLOURS['white'])

        # Position
        pos_colour = self._pos_colour(team['pos'])
        draw.text((2, y_off + 9), f"P{team['pos']}", font=self.FONTS['sm_bold'], fill=pos_colour)

        # Short team name
        draw.text((22, y_off + 9), team['short_name'], font=self.FONTS['sm_bold'], fill=self.COLOURS['white'])

        # Wins badge
        if team.get('wins', 0) > 0:
            win_text = f"{team['wins']}W"
            draw.text((48, y_off + 9), win_text, font=self.FONTS['sm'], fill=self.COLOURS['green'])

        # Full name (truncated, grey)
        full = team['name'][:11].upper()
        draw.text((2, y_off + 18), full, font=self.FONTS['sm'], fill=self.COLOURS['grey_light'])

        # Points
        draw.text((2, y_off + 25), f"{team['points']} PTS", font=self.FONTS['sm'], fill=self.COLOURS['white'])

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
