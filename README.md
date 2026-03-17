# Raspberry Pi LED Matrix Sports Scoreboard

Display live hockey and basketball game scores, future start times, standings, etc. on an LED matrix driven by a Raspberry Pi.

Hardware requirements, installation instructions (with and without Docker), and configuration breakdown are below.

## Credits
Forked from [Gidger rpi led sports scoreboard](https://github.com/gidger/rpi-led-sports-scoreboard)
F1 pulled from [MAX-POW3R fork of Gidger](https://github.com/MAX-P0W3R/rpi-led-nhl-scoreboard) with some adjustments to make standings show the same as other sports.

**Leagues Implemented:**
- NHL 🏒
- NBA 🏀
- PWHL 🏒
- MLS ⚽
- English Premier League ⚽
- La Liga ⚽
- Bundesliga ⚽
- Serie A ⚽
- Ligue 1 ⚽
- F1 🏎️

### [Watch Demo on YouTube](https://www.youtube.com/watch?v=BjqVBXsv_c8)
[![Scoreboard Demo](https://img.youtube.com/vi/BjqVBXsv_c8/maxresdefault.jpg)](https://www.youtube.com/watch?v=BjqVBXsv_c8)

### Additional Examples
<img src="https://github.com/gidger/rpi-led-sports-scoreboard/blob/83b0bbb9454c9596226d4732942d96ae19585074/examples/ex_nhl_fav_team_next_game.jpg" width="400"/> <img src="https://github.com/gidger/rpi-led-sports-scoreboard/blob/83b0bbb9454c9596226d4732942d96ae19585074/examples/ex_nhl_game_not_started.jpg" width="400"/>
<img src="https://github.com/gidger/rpi-led-sports-scoreboard/blob/83b0bbb9454c9596226d4732942d96ae19585074/examples/ex_nhl_game_in_progress.jpg" width="400"/> <img src="https://github.com/gidger/rpi-led-sports-scoreboard/blob/83b0bbb9454c9596226d4732942d96ae19585074/examples/ex_nhl_game_in_progress_goal_scored.jpg" width="400"/>
<img src="https://github.com/gidger/rpi-led-sports-scoreboard/blob/83b0bbb9454c9596226d4732942d96ae19585074/examples/ex_nhl_standings_wildcard.jpg" width="400"/> <img src="https://github.com/gidger/rpi-led-sports-scoreboard/blob/83b0bbb9454c9596226d4732942d96ae19585074/examples/ex_nba_standings_conference.jpg" width="400"/>
<img src="https://github.com/gidger/rpi-led-sports-scoreboard/blob/83b0bbb9454c9596226d4732942d96ae19585074/examples/ex_nba_fav_team_next_game.jpg" width="400"/> <img src="https://github.com/gidger/rpi-led-sports-scoreboard/blob/83b0bbb9454c9596226d4732942d96ae19585074/examples/ex_nba_game_in_progress_half.jpg" width="400"/>
<img src="https://github.com/gidger/rpi-led-sports-scoreboard/blob/1b16f59d4b9c3e7d6918aaa103db308129f0171a/examples/ex_pwhl_game_splash.jpg" width="400"/> <img src="https://github.com/gidger/rpi-led-sports-scoreboard/blob/1b16f59d4b9c3e7d6918aaa103db308129f0171a/examples/ex_pwhl_game_not_started.jpg" width="400"/>

## Note: v5.0.0
This repository has been renamed from *rpi-led-nhl-scoreboard* to *rpi-led-sports-scoreboard* reflecting that additional leagues and sports are now supported.

## Contents
1. [Hardware Required](#hardware)
1. [Installation Instructions](#install)
1. [Scenes](#scenes) 
1. [Configuration](#config) 

<a name="hardware"/>

## Hardware Required
1. A Raspberry Pi Zero 2W and all Pi 3 or 4 models should work. The Pi 5 is currently unsupported due to a critical dependency being incompatible with that device.
1. An [Adafruit RGB Matrix Bonnet](https://www.adafruit.com/product/3211) (recommended) or [RGB Matrix HAT + RTC](https://www.adafruit.com/product/2345).
1. HUB75 type 32x64 RGB LED matrix. These can be found at electronics hobby shops (or shipped from China for a lot cheaper). I recommend heading to a shop to purchase if you're unsure of exactly what you need.
1. An appropriate power supply. A 5V 4A power supply should suffice, but I offer the same advice as the LED matrix. I'm currently using a 5V 8A power supply as that's what I had lying around.
1. **OPTIONAL**, but recommended: A soldering iron, solder, and a short wire.

<a name="install"/>

## Installation Instructions
These instructions assume some very basic knowledge of electronics and Linux command line navigation. For additional details on driving an RGB matrix with a Raspberry Pi, check out [my fork of hzeller's rpi-rgb-led-matrix repo](https://github.com/gidger/rpi-rgb-led-matrix-python3.12-fix/) (it's the submodule used in this project).

As of release v3.0.0, the recommended installation method for this project leverages Docker. Instructions are provided for installation with or without Docker.

### Initial Setup: All Options
Any installation will need to start with these steps:

0. **OPTIONAL**, but recommended: Solder a jumper wire between GPIO4 and GPIO18 on the Bonnet or HAT board. This will allow you to get the best image quality later in the setup.

1. On your personal computer, use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash an SD card with Raspberry Pi OS Lite (64 bit). During this process, be sure to...
    - Set a password (keep username as "pi").
    - Set your time zone.
    - Specify WiFi credentials.
    - Enable SSH via password authentication.
    
    See full Raspberry Pi Imager getting started guide [here](https://www.raspberrypi.com/documentation/computers/getting-started.html#raspberry-pi-imager).

1. Remove the SD card from your computer and insert it into your Raspberry Pi. 

1. Assemble all hardware per [these instructions](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/matrix-setup) (steps 1 - 5).

1. Plug in your Raspberry Pi. From your personal computer, SSH into it and enter the password you set when prompted. These instructions will assume the default user of "pi" and device name of "raspberrypi". The command would look like this:
    ```bash
    ssh pi@raspberrypi.local
    ```

1. If you completed step 0 disable on-board sound to take advantage of the increased image quality. If you didn't complete step 0, skip this step.
    ```bash
    echo "blacklist snd_bcm2835" | sudo tee -a /etc/modprobe.d/alsa-blacklist.conf
    ```

1.  Update built-in packages.
    ```bash
    sudo apt-get update && sudo apt-get upgrade -y
    ```

### Option 1: Docker (Recommended)

7. Install Docker via installation script.
    ```bash
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    ```

    Then add the current user to the "docker" group. This will enable us to run "docker" commands without sudo.
    ```bash
    sudo usermod -aG docker $USER
    ```

1. Reboot your Raspberry Pi.
    ```bash
    sudo reboot
    ```
    Wait a couple minutes, then SSH back into your Raspberry Pi.
    ```bash
    ssh pi@raspberrypi.local
    ```

1. Clone this repository, including submodules.
    ```bash
    git clone --recursive https://github.com/gidger/rpi-led-sports-scoreboard.git
    ```

1. Navigate to the repository we just cloned.
    ```bash
    cd rpi-led-sports-scoreboard
    ```

1. **If you're using a Raspberry Pi 4, skip this step.** If you're using a Raspberry Pi Zero 2W, 3B, or older, you'll need to update hardware_config.gpio_slowdown in config.yaml to prevent flickering. It's recommended that you reduce the value by 1 each test and try every option to see what looks best for your hardware.

1. **If you completed Step 0, skip this step.** If not, you'll need to update hardware_config.hardware_mapping in config.yaml to match the following:
    ```yaml
    hardware_mapping: 'adafruit-hat'
    ```

1. Update config.yaml with your preferred scoreboard behaviour. Don't worry, you can freely edit these settings at any time. Recommend setting a favourite team at the minimum. See the [Configuration](#config) section for more details.

1. Start scoreboard. It will start running shortly after entering the below command. The scoreboard will automatically restart after a Raspberry Pi reboot.
    ```bash
    docker compose up -d
    ```

1. Done!

### Option 2: Manual Installation

7. Install required packages.
   ```bash
    sudo apt-get install -y git make build-essential python3 python3-dev python3-venv cython3
    ```

1. Clone this repository, including submodules.
    ```bash
    git clone --recursive https://github.com/gidger/rpi-led-sports-scoreboard.git
    ```

1. Navigate to the repository we just cloned.
    ```bash
    cd rpi-led-sports-scoreboard
    ```

1. Create a Python virtual environment with the name "venv". Then activate.
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

1. Install required Python packages.
    ```bash
    pip install -r requirements.txt
    ```
    
1. Install the LED matrix Python package. First, navigate to the LED matrix library directory.
    ```bash
    cd submodules/rpi-rgb-led-matrix
    ```
    Then, build and install:
    ```bash
    make build-python PYTHON=$(which python)
    sudo make install-python PYTHON=$(which python)
    ```

1. Return to the root of your clone of this repository.
    ```bash
    cd /home/pi/rpi-led-sports-scoreboard/ 
    ```

1. **If you're using a Raspberry Pi 4, skip this step.** If you're using a Raspberry Pi Zero 2W, 3B, or older, you'll need to update hardware_config.gpio_slowdown in config.yaml to prevent flickering. It's recommended that you reduce the value by 1 each test and try every option to see what looks best for your hardware.

1. **If you completed Step 0, skip this step.** If not, you'll need to update hardware_config.hardware_mapping in config.yaml to match the following:
    ```yaml
    hardware_mapping: 'adafruit-hat'
    ```

1. Update config.yaml with your preferred scoreboard behaviour. Don't worry, you can freely edit these settings at any time. Recommend setting a favourite team for each league at the minimum. See the [Configuration](#config) section for more details.

1. Make the scoreboard script run at startup.
    ```bash
    nano ~/start-scoreboard.sh
    ```
    Paste the following:
    ```
    #!/bin/bash
    cd /home/pi/rpi-led-sports-scoreboard
    source venv/bin/activate

    n=0
    until [ $n -ge 10 ]
    do
       sudo /home/pi/rpi-led-sports-scoreboard/venv/bin/python main.py  && break
       n=$[$n+1]
       sleep 10
    done
    ```
    Save and exit.

1. Now, let's make that script executable:
    ```
    chmod +x ~/start-scoreboard.sh
    ```

1. And make it run at boot. First, enter:
    ```
    sudo crontab -e
    ```
    Then paste the following at the bottom:

    ```
    @reboot /home/pi/start-scoreboard.sh > /home/pi/cron.log 2>&1
    ```
    Save and exit.

1. Finally, test your change by rebooting your Raspberry Pi. If everything was done correctly, the scoreboard should start automatically running shortly after boot.

    ```
    sudo reboot
    ```

1. Done!

<a name="scenes"/>

## Scenes

Functionality is divided into different "scenes" that each display information on a specific topic (e.g., today's games, standings, etc.). The currently implemented scenes are detailed below.

| **Scene**                    | **Name in config.yaml scene_order** | **Description**                                                                                                                                                                                                  |
| ---------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| NHL Games                    | nhl_games                           | Displays live NHL game scores, time remaining, etc. If the game hasn't started, start time is displayed. Can optionally display games for previous day as well.                                                  |
| NHL Favourite Team Next Game | nhl_fav_team_next_game              | Displays next game details for all specified favourite teams. If game is today, displays start time. Can optionally be suppressed if game is in progress. Will not display anything if no favourite team is set. |
| NHL Standings                | nhl_standings                       | Displays standings for wild card, division, conference, and/or overall, as configured by the user. Can optionally highlight favourite team.                                                                      |
| NBA Games                    | nba_games                           | Displays live NBA game scores, time remaining, etc. If the game hasn't started, start time is displayed. Can optionally display games for previous day as well.                                                  |
| NBA Favourite Team Next Game | nba_fav_team_next_game              | Displays next game details for all specified favourite teams. If game is today, displays start time. Can optionally be suppressed if game is in progress. Will not display anything if no favourite team is set. |
| NBA Standings                | nba_standings                       | Displays standings for division and/or conference, as configured by the user. Can optionally highlight favourite team.                                                                                           |
| PWHL Games                    | pwhl_games                           | Displays live PWHL game scores, time remaining, etc. If the game hasn't started, start time is displayed. Can optionally display games for previous day as well.                                                  |
| PWHL Favourite Team Next Game | pwhl_fav_team_next_game              | Displays next game details for all specified favourite teams. If game is today, displays start time. Can optionally be suppressed if game is in progress. Will not display anything if no favourite team is set. |
| PWHL Standings                | pwhl_standings                       | Displays standings for wild card, division, conference, and/or overall, as configured by the user. Can optionally highlight favourite team.                                                                      |
| MLS Games                    | mls_games                           | Displays live PWHL game scores, time remaining, etc. If the game hasn't started, start time is displayed. Can optionally display games for previous day as well.                                                  |
| MLS Favourite Team Next Game | mls_fav_team_next_game              | Displays next game details for all specified favourite teams. If game is today, displays start time. Can optionally be suppressed if game is in progress. Will not display anything if no favourite team is set. |
| MLS Standings                | mls_standings                       | Displays standings for conference, and/or overall, as configured by the user. Can optionally highlight favourite team.                                                                      |
| Premier League Games                    | epl_games                           | Displays live PWHL game scores, time remaining, etc. If the game hasn't started, start time is displayed. Can optionally display games for previous day as well.                                                  |
| Premier League Favourite Team Next Game | epl_fav_team_next_game              | Displays next game details for all specified favourite teams. If game is today, displays start time. Can optionally be suppressed if game is in progress. Will not display anything if no favourite team is set. |
| Premier League Standings                | epl_standings                       | Displays overall standings, as configured by the user. Can optionally highlight favourite team.                                                                      |
| La Liga Games                    | ll_games                           | Displays live PWHL game scores, time remaining, etc. If the game hasn't started, start time is displayed. Can optionally display games for previous day as well.                                                  |
| La Liga Favourite Team Next Game | ll_fav_team_next_game              | Displays next game details for all specified favourite teams. If game is today, displays start time. Can optionally be suppressed if game is in progress. Will not display anything if no favourite team is set. |
| La Liga Standings                | ll_standings                       | Displays overall standings, as configured by the user. Can optionally highlight favourite team.                                                                      |
| Bundesliga Games                    | bl_games                           | Displays live PWHL game scores, time remaining, etc. If the game hasn't started, start time is displayed. Can optionally display games for previous day as well.                                                  |
| Bundesliga Favourite Team Next Game | bl_fav_team_next_game              | Displays next game details for all specified favourite teams. If game is today, displays start time. Can optionally be suppressed if game is in progress. Will not display anything if no favourite team is set. |
| Bundesliga Standings                | bl_standings                       | Displays overall standings, as configured by the user. Can optionally highlight favourite team.                                                                      |
| Serie A Games                    | sa_games                           | Displays live PWHL game scores, time remaining, etc. If the game hasn't started, start time is displayed. Can optionally display games for previous day as well.                                                  |
| Serie A Favourite Team Next Game | sa_fav_team_next_game              | Displays next game details for all specified favourite teams. If game is today, displays start time. Can optionally be suppressed if game is in progress. Will not display anything if no favourite team is set. |
| Serie A Standings                | sa_standings                       | Displays overall standings, as configured by the user. Can optionally highlight favourite team.                                                                      |
| Ligue 1 Games                    | l1_games                           | Displays live PWHL game scores, time remaining, etc. If the game hasn't started, start time is displayed. Can optionally display games for previous day as well.                                                  |
| Ligue 1 Favourite Team Next Game | l1_fav_team_next_game              | Displays next game details for all specified favourite teams. If game is today, displays start time. Can optionally be suppressed if game is in progress. Will not display anything if no favourite team is set. |
| Ligue 1 Standings                | l1_standings                       | Displays overall standings, as configured by the user. Can optionally highlight favourite team.                                                                      |
| Formula 1 Next Race              | f1_next_race                       | Displays next scheduled race                                                                      |
| Formula 1 Driver Standings       | f1_driver_standings                | Displays current driver standings                                                                      |
| Formula 1 Constructor Standings  | f1_constructor_standings           | Displays current constructor standings                                                                      |
| Formula 1 Race Weekend           | f1_race_weekend                    | Displays race information                                                                    |
| Formula 1 Race Preview           | f1_race_preview                    | Displays race preview                                                                    |


<a name="config"/>

## Configuration

The scoreboard can be customized to meet your specific needs and preferences. Each scene has their own settings that can be used to fine tune behaviour. Additionally, there's general settings that apply to all scenes. The following sections details what can be edited in config.yaml to fine tune your scoreboard experience. All non hardware configuration settings can be updated without restarting the scoreboard. Scene changes will take effect the next time that scene is displayed.

### Web Access
Scene selection can be done by accessing the host webpage on port 80 and selecting desired scenes, then clicking Save and apply. This will update the config.yaml to only include your desired scenes while avoiding commented out lines. Please note: the changes to the config.yaml scenes will not go into effect until it has iterated through the previously selected scenes once it starts.

### General

These settings impact general scoreboard operations and are not tied to any specific scene.

| **Setting in config.yaml**        | **Description**                                                                                                                                                                                                                                    | **Options**                                                                                                                                                                                                                           | **Additional Notes**                                                                                                                                             |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| scene_order                       | Order of scenes to display. Any number and order of scenes can be specified. They should be provided as elements in a list. This scene order will repeat infinitely.                                                                               | N/A, freeform                                                                                                                                                                                                                         | Must ensure that the correct names listed in the table above are used.                                                                                           |
| favourite_teams.\<league>         | Notes the users favourite team(s). Any number can be specified for each league. They should be provided as elements in a list.                                                                                                                     | N/A, freeform                                                                                                                                                                                                                         | Should be provided as the team abbreviation in all caps.                                                                                                         |
| alt_logos.\<league>               | Notes if any alternative logos should be used for specific teams. A user can provide their own alternative logos by placing them in the correct teams_alt directory following the standard format. A small number of alt logos have been included. | N/A, freeform                                                                                                                                                                                                                         | User should provide a key value pair of team abbreviation and wanted alt logo.<br>E.g., "BOS: 1924" would set display BOS_1924.png in place of the default logo. |
| brightness.brightness_mode        | How the brightness should be determined.                                                                                                                                                                                                           | <ul><li>auto (default): Automatically determine and set brightness based on the time of day. Max brightness of brightness.max_brightness is achieved at noon</li><li>static: Static brightness of brightness.max_brightness</li></ul> |                                                                                                                                                                  |
| brightness.max_brightness         | Max brightness that the matrix will display in any mode.                                                                                                                                                                                           | Any integer 15 ≤ x ≤ 100<br> Default 100                                                                                                                                                                                              |                                                                                                                                                                  |
| hardware_config.hardware_mappings | Hardware mapping per the rpi-rgb-led-matrix settings.                                                                                                                                                                                              | <ul><li>adafruit-hat-pwm (default)</li><li>adafruit-hat</li><li>...</li></ul>                                                                                                                                                         | See submodule repository for more information.                                                                                                                   |
| hardware_config.gpio_slowdown     | GPIO slowdown per the rpi-rgb-led-matrix settings.                                                                                                                                                                                                 | <ul><li>4 (detaulf)</li><li>3</li><li>2</li><li>1</li><li>0</li>                                                                                                                                                                      | See submodule repository for more information.                                                                                                                   |

### All Scenes

These settings impact specific scenes and are found in all (most) specific scene settings. Each scene can be edited independently.

| **Setting in config.yaml**          | **Description**                                                                                    | **Options**                                                                                                                                                                                                                            | **Additional Notes**                                                                              |
| ----------------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| ...\<scene>.transition              | Transition that should be used when moving between scenes (or between elements in the same scene). | <ul><li>modern (Default): Horizontal slide with a fade to black between scene elements</li><li>fade: Fade to black between scene elements without any horizontal motion</li><li>cut: Simple jump cut, no animated transition</li></ul> | Recommend that you use the same transition for all scenes for visual consistency, but you do you. |
| ...\<scene>.splash.display_splash   | If the splash should be displayed before the scene.                                                | <ul><li>True (Default)</li><li>False</li></ul>                                                                                                                                                                                         | Not relevant for favourite team next game scenes.                                                 |
| ...\<scene>.splash_display_duration | How many seconds the splash should be displayed for.                                               | Any number > 0<br>Default 2                                                                                                                                                                                                            | If  \<scene>.splash.display_splash = False, this setting is irrelevant.                           |


### Scene Specific

These setting impact individual scenes only and are (generally) unique to that scene.

| **Relevant Scene**       | **Setting in config.yaml**                                     | **Description**                                                                                                                       | **Options**                                                    | **Additional Notes**                                                                  |
| ------------------------ | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Games                    | ...games.game_display_duration                                 | How many seconds each game should be displayed for.                                                                                   | Any number > 0<br> Default 3.5                                 |                                                                                       |
| Games                    | ...games.score_alerting.score_coloured                         | If when a team scores, their number should be highlighted red alerting a user to the score increase.                                  | <ul><li>True (Default)</li><li>False</li></ul>                 |                                                                                       |
| Games                    | ...games.score_alerting.score_fade_animation                   | If when a team scores, their number should fade back to white before moving to the next scene element. Will remain red if false.      | <ul><li>True (Default)</li><li>False</li></ul>                 | If  score_fade_animation = False, this setting is irrelevant.                         |
| Games                    | ...games.rollover.rollover_start_time_local                    | Time of day to start reporting on that days games.                                                                                    | Any time in 'HH:MM' format<br>Default 07:00                    |                                                                                       |
| Games                    | ...games.rollover.show_completed_games_until_rollover_end_time | If games for both yesterday and today should be displayed when time is between rollover_start_time_local and rollover_end_time_local. | <ul><li>True (Default)</li><li>False</li>                      |                                                                                       |
| Games                    | ...games.rollover.rollover_end_time_local                      | Time of day to stop reporting on yesterdays games.                                                                                    | Any time in 'HH:MM' format<br>Default 12:00                    | If  show_completed_games_until_rollover_end_time = False, this setting is irrelevant. |
| Favourite Team Next Game | ...fav_team_next_games.display_duration                        | How many seconds to display the next game info for each favourite team.                                                               | Any number > 0<br> Default 3.5                                 |                                                                                       |
| Favourite Team Next Game | ...fav_team_next_games.display_if_in_progress                  | If the next game should be displayed when the favourite team is currently playing.                                                    | <ul><li>False (Default)</li><li>True</li>                      | If True, the next game will be displayed with 'Ipr' in place of a date or time.       |
| Standings                | ...standings.scroll.scroll_pause_duration                      | How many seconds to pause once a team has been fully scrolled on/off the matrix.                                                      | Any number > 0<br> Default 1                                   |                                                                                       |
| Standings                | ...standings.scroll.scroll_frame_duration                      | How long to wait between frames of the scroll animation.                                                                              | Any number<br> Default 0.075                                   | The higher this number, the slower the scroll animation.                              |
| Standings                | ...standings.highlight_fav_teams                               | If favourite team(s) should be highlighted yellow in the standings.                                                                   | <ul><li>True (Default)</li><li>False</li></ul>                 |                                                                                       |
| Standings                | ...standings.display_for                                       | Which standings should be displayed (division, conference, etc.).                                                                     | See options in config.yaml. Comment/uncomment lines as needed. |                                                                                       |
