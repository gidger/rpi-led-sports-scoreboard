from ..scene import Scene
from setup.matrix_setup import matrix, matrix_options
from data.f1_data import get_next_race
from utils.data_utils import read_yaml
from PIL import Image, ImageDraw
import time


class F1NextRaceScene(Scene):
    """
    Displays upcoming race weekend information across two pages:
      Page 1 — Circuit name, country, round number, race date
      Page 2 — Qualifying date/time and race time (local circuit time where available)

    Reads settings from config.yaml under scene_settings.f1.next_race.
    """

    # F1 team colours indexed by constructorId, used for the round pip accent
    TEAM_COLOURS = {
        'mercedes':       (0, 210, 190),
        'red_bull':       (30, 65, 255),
        'ferrari':        (220, 0, 0),
        'mclaren':        (255, 135, 0),
        'aston_martin':   (0, 110, 60),
        'alpine':         (0, 90, 255),
        'williams':       (0, 130, 200),
        'rb':             (30, 65, 255),
        'kick_sauber':    (0, 180, 60),
        'haas':           (180, 180, 180),
    }

    def __init__(self):
        super().__init__()
        self.image = Image.new('RGB', (matrix_options.cols, matrix_options.rows))
        self.draw  = ImageDraw.Draw(self.image)
        self.race_data = None

    # ------------------------------------------------------------------
    # Public entry point called by main.py
    # ------------------------------------------------------------------

    def display_scene(self):
        cfg = read_yaml('config.yaml')['scene_settings']['f1']['next_race']
        display_dur = cfg.get('display_duration', 6)

        self.race_data = get_next_race()
        if not self.race_data:
            return

        # Optional splash
        if cfg.get('splash', {}).get('display_splash', True):
            self._show_splash(cfg['splash'].get('splash_display_duration', 2))

        # Page 1 — Circuit overview
        self._draw_circuit_page()
        matrix.SetImage(self.image)
        time.sleep(display_dur)

        # Page 2 — Session schedule
        self._draw_schedule_page()
        matrix.SetImage(self.image)
        time.sleep(display_dur)

    # ------------------------------------------------------------------
    # Splash
    # ------------------------------------------------------------------

    def _show_splash(self, duration):
        """Full-screen F1 logo splash with 'NEXT RACE' subtitle."""
        splash = Image.new('RGB', (matrix_options.cols, matrix_options.rows), self.COLOURS['black'])
        draw   = ImageDraw.Draw(splash)

        try:
            logo = Image.open('assets/images/f1/league/f1.png').convert('RGBA')
            logo = logo.resize((32, 14), Image.Resampling.LANCZOS)
            splash.paste(logo, (16, 3), logo)
        except Exception:
            draw.text((22, 4), 'F1', font=self.FONTS['lrg_bold'], fill=self.COLOURS['red'])

        label   = 'NEXT RACE'
        label_x = (matrix_options.cols - len(label) * 5) // 2
        draw.text((label_x, 20), label, font=self.FONTS['sm'], fill=self.COLOURS['white'])

        matrix.SetImage(splash)
        time.sleep(duration)

    # ------------------------------------------------------------------
    # Page 1 — Circuit
    # ------------------------------------------------------------------

    def _draw_circuit_page(self):
        """
        Layout (64×32):
          Row 0–7   Red header bar with country name
          Row 9–15  Circuit short name
          Row 17–23 Round badge  e.g. "RND 3/24"
          Row 25–31 Race date    e.g. "MAR 16"
        """
        r = self.race_data
        self.draw.rectangle([(0, 0), (64, 32)], fill=self.COLOURS['black'])

        # --- Header bar ---
        self.draw.rectangle([(0, 0), (64, 7)], fill=self.COLOURS['red'])
        country = r['country'].upper()[:12]            # Truncate long names
        self.draw.text((2, 0), country, font=self.FONTS['sm_bold'], fill=self.COLOURS['white'])

        # --- Circuit name ---
        circuit = r['locality'].upper()[:13]
        self.draw.text((2, 9), circuit, font=self.FONTS['sm'], fill=self.COLOURS['grey_light'])

        # --- Round badge ---
        rnd_text = f"RND {r['round']}/{r['total_rounds']}"
        self.draw.text((2, 17), rnd_text, font=self.FONTS['sm'], fill=self.COLOURS['yellow'])

        # --- Race date ---
        try:
            dt    = self.race_data['date']                    # "2026-03-15"
            month = ['JAN','FEB','MAR','APR','MAY','JUN',
                     'JUL','AUG','SEP','OCT','NOV','DEC'][int(dt[5:7]) - 1]
            day   = str(int(dt[8:10]))
            self.draw.text((2, 25), f"{month} {day}", font=self.FONTS['sm'], fill=self.COLOURS['white'])
        except Exception:
            self.draw.text((2, 25), r['date'], font=self.FONTS['sm'], fill=self.COLOURS['white'])

        matrix.SetImage(self.image)

    # ------------------------------------------------------------------
    # Page 2 — Session schedule
    # ------------------------------------------------------------------

    def _draw_schedule_page(self):
        """
        Layout:
          Row 0–7   Red header bar "SCHEDULE"
          Row 9–15  QUALI  date + time (UTC)
          Row 17–23 Divider line
          Row 19–25 RACE   date + time (UTC)
          Row 27–31 Small UTC note
        """
        r = self.race_data
        self.draw.rectangle([(0, 0), (64, 32)], fill=self.COLOURS['black'])

        # Header
        self.draw.rectangle([(0, 0), (64, 7)], fill=self.COLOURS['red'])
        self.draw.text((2, 0), 'SCHEDULE', font=self.FONTS['sm_bold'], fill=self.COLOURS['white'])

        # Qualifying row
        if r.get('quali_date'):
            q_label = f'{r['quali_date']} {r['quali_time']}'
            self.draw.text((2, 9),  'Q:', font=self.FONTS['sm'], fill=self.COLOURS['grey_light'])
            self.draw.text((14, 9), q_label, font=self.FONTS['sm'], fill=self.COLOURS['white'])
        else:
            self.draw.text((2, 9), 'Q: TBD', font=self.FONTS['sm'], fill=self.COLOURS['grey_dark'])

        # Thin separator
        self.draw.line([(0, 18), (64, 18)], fill=self.COLOURS['grey_dark'])

        # Race row
        race_label = f'{r['date']} {r['time']}'
        self.draw.text((2, 20),  'R:', font=self.FONTS['sm'], fill=self.COLOURS['grey_light'])
        self.draw.text((14, 20), race_label, font=self.FONTS['sm'], fill=self.COLOURS['white'])

        # UTC footnote
        #self.draw.text((2, 27), 'TIMES UTC', font=self.FONTS['sm'], fill=self.COLOURS['grey_dark'])

        matrix.SetImage(self.image)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fmt_session(date_str, time_str):
        """Returns e.g. 'MAR 15 14:00' from '2026-03-15' and '14:00:00'."""
        try:
            month = ['JAN','FEB','MAR','APR','MAY','JUN',
                     'JUL','AUG','SEP','OCT','NOV','DEC'][int(date_str[5:7]) - 1]
            day   = str(int(date_str[8:10]))
            hhmm  = time_str[:5] if time_str else '??:??'
            return f"{month} {day} {hhmm}"
        except Exception:
            return date_str
