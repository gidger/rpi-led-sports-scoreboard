# Raspberry Pi LED Matrix Formula 1 Scoreboard

Display live Formula 1 race weekends, championship standings, upcoming race info, and the iconic F1 starting lights sequence on a 64×32 LED matrix driven by a Raspberry Pi.

This project is a fork of [gidger/rpi-led-sports-scoreboard](https://github.com/gidger/rpi-led-sports-scoreboard), adapted to support Formula 1 exclusively using the [Jolpica/Ergast F1 API](https://api.jolpi.ca/).

Hardware requirements, installation instructions, and configuration details are below.

**Scenes Implemented:**
- F1 Next Race 🗓️
- F1 Race Weekend (Qualifying Grid / Race Results) 🏁
- F1 Driver Standings (WDC) 🏆
- F1 Constructor Standings (WCC) 🏗️
- F1 Race Preview & Starting Lights 🚦

## Contents
1. [Hardware Required](#hardware)
1. [Installation Instructions](#install)
1. [Scenes](#scenes)
1. [Configuration](#config)

---

<a name="hardware"/>

## Hardware Required
1. A Raspberry Pi Zero 2W and all Pi 3 or 4 models should work. The Pi 5 is currently unsupported due to a critical dependency being incompatible with that device.
1. An [Adafruit RGB Matrix Bonnet](https://www.adafruit.com/product/3211) (recommended) or [RGB Matrix HAT + RTC](https://www.adafruit.com/product/2345).
1. HUB75 type 32x64 RGB LED matrix. These can be found at electronics hobby shops or online.
1. An appropriate power supply. A 5V 4A supply should suffice; 5V 8A gives comfortable headroom.
1. **OPTIONAL**, but recommended: A soldering iron, solder, and a short wire.

---

<a name="install"/>

## Installation Instructions

These instructions assume basic knowledge of Linux command line navigation. For additional detail on driving an RGB matrix with a Raspberry Pi, see [gidger's fork of hzeller's rpi-rgb-led-matrix repo](https://github.com/gidger/rpi-rgb-led-matrix-python3.12-fix/) (the submodule used in this project).

### Initial Setup: All Options

0. **OPTIONAL**, but recommended: Solder a jumper wire between GPIO4 and GPIO18 on the Bonnet or HAT board for best image quality.

1. On your personal computer, use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash an SD card with **Raspberry Pi OS Lite (64-bit)**. During this process, be sure to:
    - Set a password (keep username as `pi`)
    - Set your time zone
    - Specify WiFi credentials
    - Enable SSH via password authentication

1. Insert the SD card into your Raspberry Pi and assemble hardware per [these instructions](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/matrix-setup) (steps 1–5).

1. SSH into your Pi:
    ```bash
    ssh pi@raspberrypi.local
    ```

1. If you completed step 0, disable on-board sound:
    ```bash
    echo "blacklist snd_bcm2835" | sudo tee -a /etc/modprobe.d/alsa-blacklist.conf
    ```

1. Update built-in packages:
    ```bash
    sudo apt-get update && sudo apt-get upgrade -y
    ```

---

### Option 1: Docker (Recommended)

6. Install Docker:
    ```bash
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    ```

1. Reboot, then SSH back in:
    ```bash
    sudo reboot
    # wait ~2 minutes
    ssh pi@raspberrypi.local
    ```

1. Clone this repository including submodules:
    ```bash
    git clone --recursive https://github.com/MAX-P0W3R/rpi-led-nhl-scoreboard.git formula1-led-matrix
    cd formula1-led-matrix
    ```

1. **Pi Zero 2W / Pi 3 or older only:** Reduce `hardware_config.gpio_slowdown` in `config.yaml` to prevent flickering. Try values 4 → 3 → 2 until stable.

1. **If you skipped step 0:** Update `config.yaml`:
    ```yaml
    hardware_mapping: 'adafruit-hat'
    ```

1. Set your favourite drivers and preferred scene order in `config.yaml`. See the [Configuration](#config) section.

1. Start the scoreboard:
    ```bash
    docker compose up -d
    ```

1. Done! The scoreboard will restart automatically after a reboot.

---

### Option 2: Manual Installation

6. Install required packages:
    ```bash
    sudo apt-get install -y git make build-essential python3 python3-dev python3-venv cython3
    ```

1. Clone this repository including submodules:
    ```bash
    git clone --recursive https://github.com/MAX-P0W3R/rpi-led-nhl-scoreboard.git formula1-led-matrix
    cd formula1-led-matrix
    ```

1. Create and activate a Python virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

1. Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

1. Build and install the LED matrix library:
    ```bash
    cd submodules/rpi-rgb-led-matrix
    make build-python PYTHON=$(which python)
    sudo make install-python PYTHON=$(which python)
    cd /home/pi/formula1-led-matrix/
    ```

1. **Pi Zero 2W / Pi 3 or older only:** Reduce `hardware_config.gpio_slowdown` in `config.yaml`.

1. **If you skipped step 0:** Set `hardware_mapping: 'adafruit-hat'` in `config.yaml`.

1. Set up auto-start on boot:
    ```bash
    nano ~/start-scoreboard.sh
    ```
    Paste the following:
    ```bash
    #!/bin/bash
    cd /home/pi/formula1-led-matrix
    source venv/bin/activate

    n=0
    until [ $n -ge 10 ]
    do
       sudo /home/pi/formula1-led-matrix/venv/bin/python main.py && break
       n=$[$n+1]
       sleep 10
    done
    ```
    Save, then make it executable:
    ```bash
    chmod +x ~/start-scoreboard.sh
    ```

1. Schedule it to run at boot:
    ```bash
    sudo crontab -e
    ```
    Add to the bottom:
    ```
    @reboot /home/pi/start-scoreboard.sh > /home/pi/cron.log 2>&1
    ```

1. Reboot to test:
    ```bash
    sudo reboot
    ```

1. Done!

---

<a name="scenes"/>

## Scenes

Each scene displays a specific type of F1 information on the matrix. Scenes cycle in the order defined in `config.yaml`.

| **Scene** | **Name in config.yaml** | **Description** |
|---|---|---|
| F1 Next Race | `f1_next_race` | Two-page display: page 1 shows circuit name, country, and round number. Page 2 shows qualifying and race session times in UTC. |
| F1 Race Weekend | `f1_race_weekend` | Automatically detects the current point in the race weekend. Shows the qualifying grid if between qualifying and the race, otherwise shows the latest race results. Cycles through the top 10 drivers one at a time. Podium positions highlighted in gold/silver/bronze. Favourite drivers highlighted in yellow. |
| F1 Driver Standings | `f1_driver_standings` | Scrolling WDC standings showing position, driver code, constructor, points, and win count for the top 10. Favourite drivers highlighted in yellow. Automatically falls back to the previous season if the current season has no completed rounds yet. |
| F1 Constructor Standings | `f1_constructor_standings` | Scrolling WCC standings showing position, team name, points, and win count for all 10 constructors. Automatically falls back to the previous season if needed. |
| F1 Race Preview | `f1_race_preview` | Displays a race card with circuit info for the upcoming Grand Prix, followed by the F1 starting lights sequence: 5 red lights illuminate one by one (right-to-left), then go out after a random delay mimicking a real F1 start. Ends with a green "GO!!" flash. |

---

<a name="config"/>

## Configuration

All scoreboard behaviour is controlled via `config.yaml`. Hardware settings require a restart; all other settings take effect at the start of the next scene cycle.

### General

| **Setting** | **Description** | **Options** |
|---|---|---|
| `scene_order` | Ordered list of scenes to display, repeating infinitely. | Any combination of the scene names listed above. |
| `favourite_drivers` | Your favourite driver(s) by three-letter code (e.g. `NOR`, `HAM`). Used to highlight drivers in standings and race weekend scenes. | Any number of driver codes in all caps. |
| `brightness.brightness_mode` | How brightness is determined. | `auto`: varies by time of day, peak at noon. `static`: fixed at `max_brightness`. |
| `brightness.max_brightness` | Maximum brightness level. | Integer 15–100. Default `60` (recommended for indoor use). |
| `hardware_config.hardware_mapping` | Hardware mapping for the LED matrix driver. | `adafruit-hat-pwm` (default, requires GPIO4/18 solder bridge). `adafruit-hat` (no soldering required). |
| `hardware_config.gpio_slowdown` | GPIO slowdown to prevent flickering on older Pi hardware. | `4` (default, recommended for Pi Zero). Reduce if experiencing issues on Pi 3/4. |

### Scene Settings

All scenes share these common settings under `scene_settings.f1.<scene_name>`:

| **Setting** | **Description** | **Options** |
|---|---|---|
| `splash.display_splash` | Whether to show the F1 logo splash before the scene. | `True` (default), `False` |
| `splash.splash_display_duration` | Seconds to display the splash screen. | Any number > 0. Default `2`. |
| `transition` | Transition style between scene elements. | `modern` (default), `fade`, `cut` |

### Scene-Specific Settings

| **Scene** | **Setting** | **Description** | **Default** |
|---|---|---|---|
| `next_race` | `display_duration` | Seconds each page (circuit / schedule) is shown. | `6` |
| `race_weekend` | `driver_display_duration` | Seconds each driver row is displayed before moving to the next. | `3` |
| `driver_standings` | `highlight_fav_drivers` | Highlight favourite drivers in yellow. | `True` |
| `driver_standings` | `scroll.scroll_frame_duration` | Delay between scroll animation frames. Higher = slower scroll. | `0.075` |
| `driver_standings` | `scroll.scroll_pause_duration` | Seconds to pause when a new driver card is fully in view. | `1.0` |
| `constructor_standings` | `scroll.scroll_frame_duration` | Delay between scroll animation frames. | `0.075` |
| `constructor_standings` | `scroll.scroll_pause_duration` | Seconds to pause on each constructor card. | `1.0` |
| `race_preview` | `display_duration` | Seconds the race card is shown before the lights sequence begins. | `5` |
| `race_preview` | `show_starting_lights` | Whether to run the starting lights animation after the race card. | `True` |

---

## Data Sources

Live F1 data is fetched from the [Jolpica Ergast API](https://api.jolpi.ca/) — a free, no-key-required REST API for historical and current F1 data. Circuit coordinates for weather lookups are stored locally in `utils/tracks.json`, which includes all 24 circuits on the 2026 calendar.

---

## Credits

- Original scoreboard project by [gidger](https://github.com/gidger/rpi-led-sports-scoreboard)
- LED matrix driver by [hzeller](https://github.com/hzeller/rpi-rgb-led-matrix)
- F1 data via [Jolpica/Ergast API](https://api.jolpi.ca/)
