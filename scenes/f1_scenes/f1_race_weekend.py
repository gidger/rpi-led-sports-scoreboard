from ..scene import Scene
from setup.matrix_setup import matrix, matrix_options
from data.f1_data import get_latest_qualifying, get_latest_race_results, get_next_race
from utils.data_utils import read_yaml
from PIL import Image, ImageDraw
from datetime import datetime, timezone
import time


class F1RaceWeekendScene(Scene):
    """
    Weekend-aware scene that automatically shows the most relevant data:

      • Between Thursday–Saturday of a race weekend  → Qualifying grid (P1–P10)
      • Sunday of race weekend or week after          → Race results  (P1–P10)
      • Off-weekend                                   → Most recent race results

    Each driver row scrolls onto the display one by one:
        P1  VER  25pts
        P2  NOR  18pts
        ...

    Reads settings from config.yaml under scene_settings.f1.race_weekend.
    """

    # Status codes that mean a driver did not finish
    DNF_STATUSES = {'Accident', 'Collision', 'Engine', 'Gearbox', 'Hydraulics',
                    'Electrical', 'Retired', 'Mechanical', 'Suspension', 'Power Unit'}

    def __init__(self):
        super().__init__()
        self.image = Image.new('RGB', (matrix_options.cols, matrix_options.rows))
        self.draw  = ImageDraw.Draw(self.image)
        self.fav_drivers = []

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def display_scene(self):
        cfg      = read_yaml('config.yaml')
        settings = cfg['scene_settings']['f1']['race_weekend']
        self.fav_drivers = [d.upper() for d in cfg.get('favourite_drivers', [])]

        mode, data = self._decide_mode()
        if not data:
            return

        # Splash
        if settings.get('splash', {}).get('display_splash', True):
            self._show_splash(
                mode,
                settings['splash'].get('splash_display_duration', 2)
            )

        row_dur = settings.get('driver_display_duration', 3)
        self._render_results(data, mode, row_dur)

    # ------------------------------------------------------------------
    # Mode detection
    # ------------------------------------------------------------------

    def _decide_mode(self):
        """
        Returns ('qualifying' | 'race', list_of_dicts).
        Logic:
          - If today is within a qualifying window (Fri–Sat of a race weekend), show quali
          - Otherwise show most recent race results
        """
        now  = datetime.now(timezone.utc)
        next_race = get_next_race()

        show_quali = False
        if next_race and next_race.get('quali_date'):
            try:
                q_dt = datetime.strptime(next_race['quali_date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
                r_dt = datetime.strptime(next_race['date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
                # Show qualifying results in the window between quali day and race day
                if q_dt.date() <= now.date() < r_dt.date():
                    show_quali = True
            except Exception:
                pass

        if show_quali:
            data = get_latest_qualifying()
            if data:
                return 'qualifying', data

        # Default: race results
        data = get_latest_race_results()
        return 'race', data

    # ------------------------------------------------------------------
    # Splash
    # ------------------------------------------------------------------

    def _show_splash(self, mode, duration):
        label = 'QUALIFYING' if mode == 'qualifying' else 'RACE RESULT'
        splash = Image.new('RGB', (matrix_options.cols, matrix_options.rows), self.COLOURS['black'])
        draw   = ImageDraw.Draw(splash)

        try:
            logo = Image.open('assets/images/f1/league/f1.png').convert('RGBA')
            logo = logo.resize((32, 14), Image.Resampling.LANCZOS)
            splash.paste(logo, (16, 3), logo)
        except Exception:
            draw.text((22, 4), 'F1', font=self.FONTS['lrg_bold'], fill=self.COLOURS['red'])

        label_x = (matrix_options.cols - len(label) * 5) // 2
        draw.text((label_x, 20), label, font=self.FONTS['sm'], fill=self.COLOURS['white'])
        matrix.SetImage(splash)
        time.sleep(duration)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_results(self, data, mode, row_duration):
        """
        Displays driver rows one at a time, holding each for row_duration.
        Layout per frame (64×32):
          Row 0–7   Red header  "QUALI GRID" or "RACE RESULT"
          Row 9–15  Position + Driver code (highlighted yellow if fav)
          Row 17–23 Constructor short name
          Row 25–31 Best time (quali) or points scored (race)
        """
        header = 'QUALI GRID' if mode == 'qualifying' else 'RACE RESULT'
        top10  = data[:10]

        for entry in top10:
            self.draw.rectangle([(0, 0), (64, 32)], fill=self.COLOURS['black'])

            # Header bar
            self.draw.rectangle([(0, 0), (64, 7)], fill=self.COLOURS['red'])
            self.draw.text((2, 0), header, font=self.FONTS['sm_bold'], fill=self.COLOURS['white'])

            # Position
            pos_str  = str(entry['pos']).rjust(2)
            pos_colour = self._pos_colour(entry['pos'])
            self.draw.text((2, 9), f"P{pos_str}", font=self.FONTS['sm_bold'], fill=pos_colour)

            # Driver code — yellow if favourite
            code = entry.get('code', '???')
            code_colour = (self.COLOURS['yellow']
                           if code in self.fav_drivers
                           else self.COLOURS['white'])
            self.draw.text((22, 9), code, font=self.FONTS['sm_bold'], fill=code_colour)

            # Constructor
            from utils.f1_api import _CONSTRUCTOR_NAMES
            cid       = entry.get('constructor_id', '')
            team_name = _CONSTRUCTOR_NAMES.get(cid, cid[:8].upper())
            self.draw.text((2, 17), team_name, font=self.FONTS['sm'], fill=self.COLOURS['grey_light'])

            # Bottom stat — time (quali) or points (race)
            if mode == 'qualifying':
                best_time = entry.get('q3') or entry.get('q2') or entry.get('q1') or '--'
                self.draw.text((2, 25), best_time, font=self.FONTS['sm'], fill=self.COLOURS['grey_light'])
            else:
                pts_str = f"{entry.get('points', 0)} PTS"
                status  = entry.get('status', '')
                if any(dnf in status for dnf in self.DNF_STATUSES):
                    pts_str = 'DNF'
                    self.draw.text((2, 25), pts_str, font=self.FONTS['sm'], fill=self.COLOURS['red'])
                else:
                    self.draw.text((2, 25), pts_str, font=self.FONTS['sm'], fill=self.COLOURS['white'])

            matrix.SetImage(self.image)
            time.sleep(row_duration)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pos_colour(pos):
        """Gold/silver/bronze for podium, white otherwise."""
        if pos == 1:
            return (255, 209, 0)   # Gold
        if pos == 2:
            return (180, 180, 180) # Silver
        if pos == 3:
            return (180, 100, 40)  # Bronze
        return (255, 255, 255)
