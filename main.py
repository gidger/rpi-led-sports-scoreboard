
from scenes.f1_scenes.f1_race_preview import F1RacePreviewScene
from scenes.f1_scenes.f1_race_weekend import F1RaceWeekendScene
from scenes.f1_scenes.f1_next_race import F1NextRaceScene
from scenes.f1_scenes.f1_driver_standings import F1DriverStandingsScene
from scenes.f1_scenes.f1_constructor_standings import F1ConstructorStandingsScene
from setup.matrix_setup import matrix, determine_matrix_brightness
from utils import data_utils


def run_scoreboard():
    scene_mapping = {
        'f1_race_preview':        F1RacePreviewScene(),
        'f1_race_weekend':        F1RaceWeekendScene(),
        'f1_next_race':           F1NextRaceScene(),
        'f1_driver_standings':    F1DriverStandingsScene(),
        'f1_constructor_standings': F1ConstructorStandingsScene(),
    }

    while True:
        scene_order = data_utils.read_yaml('config.yaml')['scene_order']
        matrix.brightness = determine_matrix_brightness()

        for scene in scene_order:
            if scene in scene_mapping:
                scene_mapping[scene].display_scene()


if __name__ == '__main__':
    run_scoreboard()



