![MIDI Mesh Logo](data/icon_transparent.png)

# MIDI Mesh


An open-source, cross-platform MIDI sequencing application. Inspired by mesh networks.

Primarily created for Android, but can be run on desktop with native python (developed with python version 3.11.9, runs fine with 3.12).

Currently, the app has been tested on Android and Debian. However, I've attempted to provide allowances for it to 'just work' on other platforms (adjust your commands if needed). Please provide feedback if you got it working (or not) on other platforms.

![MIDI Mesh](assets/Screenshot.png)


## Android:


Download the APK from the Packages page and install on-device or via ADB.

If you're adventurous, feel free to build for Android using Buildozer (or p4a directly) using the relevant documentation for your build environment of choice..


## To run out of the box on desktop:


On Debian systems, install the dependancies for python-rtmidi:


`sudo apt update`

`sudo apt install build-essential libasound2-dev libjack-jackd2-dev`


### Clone the repository:


`git clone https://github.com/EmergentProperly/MIDIMesh.git`

`cd /MIDIMesh`


### Create the environment:


`python3 -m venv venv`

`source venv/bin/activate`


### Install requirements.txt:


`pip install -r requirements.txt`


### Run:

`python3 main.py`





## ROADMAP (to 1.0):


- Whittle away the monolithic modules

- Clean up and replace some assets

- Fix emergent bugs

- ~~Tackle the recently introduced 16kb pagefile requirement for submission to the Play Store~~ ~~(unlikely to do this if 3rd party development is killed off for Android, priority for this is significantly reduced for now)~~ Priority for both issues is currently low.

- Look into semantic versioning requirements etc...

- 1.0

- F-Droid submssion (?)

- ...

- 2.0 to include inbuilt audio engine (synths, sampling, FX, etc)... possible shift in development towards an open source hardware device.


## Feedback:

Please share feedback regarding your experience with the app, and any issues you may have faced. I want this to be an awesome tool for creatives, so all rational feedback and/or feature requests will be considered carefully and appreciated.

Have fun!


## Licensing & Attributions:

This project is licensed under the GNU GPL v3. It utilizes several open-source libraries, including Kivy, Mido, and python-rtmidi. See NOTICES.md for full third-party license details.
