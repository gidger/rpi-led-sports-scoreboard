from ..scene import Scene
from setup.matrix_setup import matrix, matrix_options
from data.f1_data import get_next_race
from utils.data_utils import read_yaml
from PIL import Image, ImageDraw
import json
import time
import random


class F1RacePreviewScene(Scene):
    """
    Two-part scene:
      Part 1 — Race card: country, circuit, round, date (held for display_duration seconds)
      Part 2 — Starting-lights sequence:
                  5 red lights illuminate one-by-one (right-to-left)
                  Random delay (0.5–2.5 s) mimicking real F1 start
                  Lights out → green "GO!!" flash

    Can be disabled in config by setting show_starting_lights: False.
    Reads settings from config.yaml under scene_settings.f1.race_preview.
    """

    def __init__(self):
        super().__init__()
        self.image     = Image.new('RGB', (matrix_options.cols, matrix_options.rows))
        self.draw      = ImageDraw.Draw(self.image)
        self.race_data = None
        self.track_info = None

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def display_scene(self):
        cfg      = read_yaml('config.yaml')
        settings = cfg['scene_settings']['f1']['race_preview']

        display_dur  = settings.get('display_duration', 5)
        show_lights  = settings.get('show_starting_lights', True)

        self._fetch_data()

        # Part 1 — Race card
        self._draw_race_card()
        matrix.SetImage(self.image)
        time.sleep(display_dur)

        # Part 2 — Starting lights (optional)
        if show_lights:
            self._run_starting_lights()

    # ------------------------------------------------------------------
    # Data fetch
    # ------------------------------------------------------------------

    def _fetch_data(self):
        self.race_data  = get_next_race()
        self.track_info = None

        if not self.race_data:
            return

        circuit_id = self.race_data.get('circuit_id')
        try:
            with open('utils/tracks.json', 'r') as f:
                tracks = json.load(f)
            self.track_info = tracks.get(circuit_id)
            if not self.track_info:
                print(f"F1 RacePreview: No track data for '{circuit_id}'")
        except Exception as e:
            print(f"F1 RacePreview data error: {e}")

    # ------------------------------------------------------------------
    # Race card
    # ------------------------------------------------------------------

    def _draw_race_card(self):
        """
        Layout (64×32):
          Row 0–7   Red header bar with COUNTRY name
          Row 9–15  Circuit locality (grey)
          Row 17–23 Round badge     (yellow)
          Row 25–31 Race date       (white)
        """
        self.draw.rectangle([(0, 0), (64, 32)], fill=self.COLOURS['black'])

        r = self.race_data
        if not r:
            self.draw.text((2, 12), 'NO DATA', font=self.FONTS['sm'], fill=self.COLOURS['red'])
            return

        # Header bar
        self.draw.rectangle([(0, 0), (64, 7)], fill=self.COLOURS['red'])
        country = r['country'].upper()[:12]
        self.draw.text((2, 0), country, font=self.FONTS['sm_bold'], fill=self.COLOURS['white'])

        # Circuit locality
        locality = r['locality'].upper()[:13]
        self.draw.text((2, 9), locality, font=self.FONTS['sm'], fill=self.COLOURS['grey_light'])

        # Round badge
        rnd_str = f"RND {r['round']}/{r['total_rounds']}"
        self.draw.text((2, 17), rnd_str, font=self.FONTS['sm'], fill=self.COLOURS['yellow'])

        # Race date
        try:
            dt    = r['date']
            month = ['JAN','FEB','MAR','APR','MAY','JUN',
                     'JUL','AUG','SEP','OCT','NOV','DEC'][int(dt[5:7]) - 1]
            day   = str(int(dt[8:10]))
            self.draw.text((2, 25), f"{month} {day}", font=self.FONTS['sm'], fill=self.COLOURS['white'])
        except Exception:
            self.draw.text((2, 25), r.get('date', '??'), font=self.FONTS['sm'], fill=self.COLOURS['white'])

    # ------------------------------------------------------------------
    # Starting lights
    # ------------------------------------------------------------------

    def _run_starting_lights(self):
        """
        Lights illuminate right-to-left (as on a real F1 gantry),
        one per second, then go out after a random delay.
        """
        # Light x-centres (right to left): 5 lights
        light_xs = [52, 42, 32, 22, 12]

        for step in range(1, 6):
            self._draw_lights_frame(light_xs, lit=step)
            matrix.SetImage(self.image)
            time.sleep(1.0)

        # Random delay — the tension moment
        time.sleep(random.uniform(0.5, 2.5))

        # Lights out — GO!!
        self._draw_lights_out(light_xs)
        matrix.SetImage(self.image)
        time.sleep(2.0)

    def _draw_lights_frame(self, light_xs, lit):
        """Draws the F1 logo + N red lights (right-to-left fill)."""
        self.draw.rectangle([(0, 0), (64, 32)], fill=self.COLOURS['black'])
        self._draw_f1_logo(y=1, height=14)

        for i in range(lit):
            cx = light_xs[i]
            self.draw.ellipse([cx - 4, 19, cx + 4, 27], fill=self.COLOURS['red'])

    def _draw_lights_out(self, light_xs):
        """Clears all lights and shows the green GO!! message."""
        self.draw.rectangle([(0, 0), (64, 32)], fill=self.COLOURS['black'])
        self._draw_f1_logo(y=1, height=14)

        # Centre "GO!!" text on the lower half
        go_text = 'GO!!'
        go_x    = (matrix_options.cols - len(go_text) * 5) // 2
        self.draw.text((go_x, 19), go_text, font=self.FONTS['sm_bold'], fill=(0, 255, 0))

    def _draw_f1_logo(self, y, height):
        """Loads and centres the F1 logo at the given y-offset and pixel height."""
        try:
            logo = Image.open('assets/images/f1/league/f1.png').convert('RGBA')
            # Preserve aspect ratio
            orig_w, orig_h = logo.size
            new_w = int(orig_w * (height / orig_h))
            logo  = logo.resize((new_w, height), Image.Resampling.LANCZOS)
            x     = (matrix_options.cols - new_w) // 2
            self.image.paste(logo, (x, y), logo)
        except Exception:
            # Fallback text if asset is missing
            self.draw.text((22, y + 2), 'F1', font=self.FONTS['sm_bold'], fill=self.COLOURS['red'])
