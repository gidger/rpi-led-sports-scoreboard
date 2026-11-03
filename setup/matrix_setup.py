from utils import data_utils
from datetime import datetime as dt
import math


# Determine display mode from config.yaml. If display_mode is missing, fall back to 'led_matrix'.
display_mode = data_utils.read_yaml('config.yaml').get('display_mode', 'led_matrix')

# Import the appropriate RGBMatrix library based on the display_mode.
if display_mode == 'led_matrix':
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
elif display_mode == 'browser':
    from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions

# If display_mode is not recognized, raise an error.
else:
    raise ValueError(f'Unsupported display_mode: "{display_mode}". Expected "led_matrix" or "browser".')


def determine_matrix_brightness():
    """ Determines the brightness of the LED matrix.

    Returns:
        int: brightness from 1-100.
    """

    # Load brightness config settings from config.yaml.
    brightness_config = data_utils.read_yaml('config.yaml')['brightness']

    # If static brightness, simply get the brightness from config.yaml.
    if brightness_config['brightness_mode'] == 'static':
        return brightness_config['max_brightness']
    
    # If automatic brightness, calculate the brightness based on max_brightness and the current time.
    elif brightness_config['brightness_mode'] == 'auto':
        # Get hour of current time as an int 0-23.
        hour_int = dt.today().time().hour
        
        # Calculate brightness based on max_brightness and current time.
        max_brightness = brightness_config['max_brightness']
        brightness = math.ceil(max_brightness * hour_int / 12 if hour_int <= 12 else max_brightness * (24 - hour_int) / 12)
        brightness = brightness if brightness >= 15 else 15
        return brightness
    
    # If unexpected brightness_mode, fallback to max brightness.
    else:
        print(f'Unexpected brightness_mode encountered in config.yaml: {brightness_config["brightness_mode"]}. Falling back to 100%.')
        return 100

# Make matrix options object with needed settings.
matrix_options = RGBMatrixOptions()
matrix_options.rows = 32
matrix_options.cols = 64
matrix_options.chain_length = 1
matrix_options.parallel = 1
matrix_options.drop_privileges = False # Needed to ensure fonts and images load correctly.

# Hardware specific config from config.yaml.
hardware_config = data_utils.read_yaml('config.yaml')['hardware_config']
matrix_options.gpio_slowdown = hardware_config['gpio_slowdown']
matrix_options.hardware_mapping = hardware_config['hardware_mapping']

# Determine brightness.
matrix_options.brightness = determine_matrix_brightness()

# Finally, make matrix object.
matrix = RGBMatrix(options=matrix_options)
