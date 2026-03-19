# MIDI Mesh



[MIDI Mesh](assets/help_bg.png)

An open-source, cross-platform MIDI sequencing application. Inspired by mesh networks.

Primarily created for Android, but can be run on desktop with native python (developed with python version 3.11.9, runs fine with 3.12).

Currently, the app has been tested on Android and Debian. However, it should 'just work' on other platforms (adjust your commands if needed).


## Android:


Download the APK from the releases page and install on-device or via ADB.

If you're adventurous, feel free to build for Android using Buildozer (or p4a directly) using the relevant documentation.


## To run out of the box on desktop:



### Clone the ropository:


`git clone https://github.com/EmergentProperly/MIDI_Mesh`

`cd /MIDI_Mesh`


### Create the environment:


`python3 -m venv venv`

`source ./venv/bin/activate`


### Install requirements.txt:


`python3 install -r requirements.txt`


### Run:

`python3 main.py`





## ROADMAP (to 1.0):


- Whittle away the God Objects

- Clean up and replace some assets

- Fix emergent bugs

- F-Droid submssion

- Tackle the recently introduced 16kb pagefile requirement for submission to the Play Store

- Adhere to semantic versioning, public facing API etc.

- 1.0

- ...

- 2.0 to include inbuilt audio engine (synths, sampling, FX, etc).



## Feedback:


Please share feedback regarding your experience with the app, and any issues you may have faced. I want this to be an awesome tool for creatives, so all rational feedback and/or feature requests will be considered carefully and appreciated.

Have fun!
