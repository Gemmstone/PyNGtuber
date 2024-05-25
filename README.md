<div align="center">

# PyNGtuber

A PNGtuber app with lots of customizablility.

![hot icon](https://raw.githubusercontent.com/aGemmstone/PyNGtuber/master/docs/logo.png)

<!-- [![KDE Store](https://img.shields.io/badge/KDE%20Store-Install-blue?style=for-the-badge&logo=KDE&logoColor=white&labelColor=blue)](https://store.kde.org/p/2140417)  -->
[![GitHub](https://img.shields.io/badge/GitHub-Source%20Code-grey?style=for-the-badge&logo=GitHub&logoColor=white&labelColor=grey)](https://github.com/zeroxoneafour/polonium)

[![Python 3.11](https://img.shields.io/python/required-version-toml)]("https://www.python.org/downloads/release/python-3110/")
<!-- [![wayland: supported](https://img.shields.io/badge/Wayland-Ready-blue?logo=kde)](https://community.kde.org/KWin/Wayland)  -->
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://makeapullrequest.com)
[![ko-fi](https://img.shields.io/badge/-Support%20me%20on%20Ko--Fi-orange?logo=kofi&logoColor=white)](https://ko-fi.com/gemmstone)

</div>

## features

-   Works in Wayland Plasma 6.0.4 and up
-   Custom moddable tiling engine backend
-   Edit tile sizes with the integrated KWin GUI
-   Move and tile windows with your mouse and keyboard
-   Set layouts independently of desktop, activity, and screen
-   [DBus integration](https://github.com/zeroxoneafour/dbus-saver) to save layouts and configurations after logging out

## X11

X11 has been briefly tested but is not supported. If you encounter an issue running the script on X11, make sure it is reproducible in Wayland before submitting a bug report.

## building

Requires `npm` and `kpackagetool6`

Commands -

-   Build/Install/Clean - `make`
-   Build - `make build`
-   Install/Reinstall - `make install`
-   Clean build - `make clean`
-   Clean build and target - `make cleanall`

## license

Majority of this project is [GPL-3.0 licensed](https://github.com/Gemmstone/PyNGtuber/blob/master/LICENSE), please bum my code if you can use to make something better. Make sure to give credit though!



## name

Came from a comment on my old script, you can find the script and comment [here](https://store.kde.org/p/2003956)

# PyNGtuber
PNGtuber software made in Python, still in development

## Introduction

I've just started developing my own PNGtubing software, and I'm excited to make it open-source. This means it will be completely free, and I welcome contributions from the community to add new features and improve the codebase.

## Current Status Demo

https://github.com/Gemmstone/PyNGtuber/assets/31828821/fc5b1aa5-169c-4a53-8cef-9f7ddb45287b

## Python (3.11) Dependancies
- PyQt6
- pyaudio
- pillow
- PyQt6-WebEngine
- beautifulsoup4
- mido
- numpy
- pynput
- dateutils
- twitchapi
- sounddevice
- pyautogui
  
  `pip install pyqt6 pyqt6-webengine pillow pyaudio beautifulsoup4 mido numpy pynput dateutils twitchapi sounddevice pyautogui`

## Future Plans

I have ambitious plans for the software, including:

- ~~An emotion selector that's completely independent of the model.~~
- ~~A clothing selector, also completely independent.~~
- ~~Animations for hair, tails, ears, and clothing.~~
- ~~Support for GIFs and PNGs.~~
- ~~Support for various assets, such as knives, controls, and more.~~
- ~~Changing expressions, clothing, assets, etc., via keyboard shortcuts or MIDI signals.~~
- ~~3 types of mouths: open, closed, and screaming.~~
- wow i just did all of these already lol, i still have some things i wanna add, i'll list them later

I'll continue to brainstorm and add more features while keeping the software as lightweight as possible.

## Contributions

If you're interested in contributing to this project or checking out the code, feel free to get involved. Contributions are highly appreciated!

## License

This project is licensed under the GNU General Public License, version 3.0 (GPL-3.0). You can find a copy of the license in the [LICENSE](LICENSE) file.

## Getting Started

Instructions on how to set up and run the software will be provided here as the project develops.

## Feedback

Your feedback and ideas are valuable. If you have suggestions or questions, please don't hesitate to reach out.
