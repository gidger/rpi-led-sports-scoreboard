from flask import Flask, render_template, request, redirect
from ruamel.yaml import YAML
import os

app = Flask(__name__)
CONFIG_PATH = 'config.yaml'

yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)


# FORCE BOOLS TO STAY CAPITALIZED
def bool_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:bool', 
                                   u'True' if data else u'False')

yaml.representer.add_representer(bool, bool_representer)

# Grouping data for the UI
LEAGUES = {
    "NHL": ["nhl_fav_team_next_game", "nhl_games", "nhl_standings"],
    "NBA": ["nba_fav_team_next_game", "nba_games", "nba_standings"],
    "NCAA-MENS": ["ncaa_mens_fav_team_next_game", "ncaa_mens_games"],
    "NCAA-WOMENS": ["ncaa_womens_fav_team_next_game","ncaa_womens_games"],
    "PWHL": ["pwhl_fav_team_next_game", "pwhl_games", "pwhl_standings"],
    "MLS": ["mls_fav_team_next_game", "mls_games", "mls_standings"],
    "EPL": ["epl_fav_team_next_game", "epl_games", "epl_standings"],
    "LL": ["laliga_fav_team_next_game", "laliga_games", "laliga_standings"],
    "BL": ["bundesliga_fav_team_next_game", "bundesliga_games", "bundesliga_standings"],
    "SA": ["seriea_fav_team_next_game", "seriea_games", "seriea_standings"],
    "L1": ["ligue1_fav_team_next_game", "ligue1_games", "ligue1_standings"],
    "F1": ["f1_next_race", "f1_driver_standings", "f1_constructor_standings", "f1_race_weekend", "f1_race_preview"]
}

DISPLAY_NAMES = {
    "NHL": "NHL",
    "NBA": "NBA",
    "NCAA-Mens": "NCAA Mens",
    "NCAA-Womens": "NCAA Womens",
    "PWHL": "PWHL",
    "MLS": "MLS",
    "EPL": "Premier League",
    "LL": "La Liga",
    "BL": "Bundesliga",
    "SA": "Serie A",
    "L1": "Ligue 1",
    "F1": "Formula 1"
}

def format_label(scene_string):
    # Mapping of technical endings to human-readable labels
    label_map = {
        "next game": "Favorite Team Next Game",
        "games": "Games",
        "standings": "Standings",
        "next race": "Next Race",
        "driver standings": "Driver Standings",
        "race weekend": "Race Weekend",
        "race preview": "Race Preview"
    }
    
    # Split by underscore
    parts = scene_string.split('_')
    
    # Look for the last part in our map, or default to the original string
    if len(parts) > 2:
        suffix = f'{parts[-2]} {parts[-1]}'
    else:
        suffix = parts[-1]
    print(suffix)
    return label_map.get(suffix, suffix.title())

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected = request.form.getlist('scenes')
        with open(CONFIG_PATH, 'r') as f:
            data = yaml.load(f)
        
        data['scene_order'] = selected
        
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(data, f)
        return redirect('/')

    with open(CONFIG_PATH, 'r') as f:
        current_data = yaml.load(f)
        active_scenes = current_data.get('scene_order', [])

    return render_template('index.html', leagues=LEAGUES, active_scenes=active_scenes, format_label=format_label, display_names=DISPLAY_NAMES)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
