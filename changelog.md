# changelog

## 1.0

### 1.6.0

- Twitch Chat Listening for Shortcuts
- Animations selector per Asset
- Added the hability to use an HTML file as an Asset
- another change trying fix the glitching avatar issue in Windows, i have no way to test if it's fixed sadly
- Various small improvements

### 1.5.3

- -- New python dependancy (psutil) --
- Added a selector for hardware acceleration
  - Set to Disabled by default
- Made controller tracker only start when a controller is added to the model
- Automatically setting up the priority level of the program to max level
  - Hoping these 3 changes fix the glitching avatar issue in Windows, i have no way to test if it's fixed sadly

### 1.5.2

- Fixed a crash issue when deleting a model
- Fixed a startup error warning with the audio
- Added a way to select the blinking and talking status at the same time on the same asset
  - This enables support for "4 images" models (One image with eyes open mouth closed, one for eyes open mouth open, etc.)
- Added separate settings for mouse tracking in X and Y axis #1
- Added a "no animation" option
- Error fixes:
  - Fixed an error warning in the mouse tracker on closing
  - Corrected a problem that was reseting assets settings to "factory defaults"
  - Fixed a version number problem that was in 1.5.0 and 1.5.1
  - Other small fixes

### 1.4.2

- Fixed a path issue with custom assets that crashed the program when trying to load them
- Fixed some Path problems with the HTML viewer
- Added debug mode for the HTML and CSS editor so you can edit these files in real time to test stuff
- Settings, Assets and Models are now saved in .config or AppData so data isn't lost when updating manually
  - the program can now auto-update with just a single click!
  - Fixed the scale slider
  - Small fixes

### 1.4.1

- Fixed some Path problems with the HTML viewer
- Added debug mode for the HTML and CSS editor so you can edit these files in real time to test stuff
- Settings, Assets and Models are now saved in .config or AppData so data isn't lost when updating manually
  - the program can now auto-update with just a single click!
  - Fixed the scale slider
  - Small fixes

### 1.4.0

- Settings, Assets and Models are now saved in .config or AppData so data isn't lost when updating 
- the program can now auto-update with just a single click!
- Fixed the scale slider
- Small fixes

### 1.3.0

- Expanded mouse tracking and fixed performance issues with it
  - Now you can use the mouse to give the assets a paralax effect so you can make your avatar look to your cursor
- Added a button to disable mouse tracking
- Fixed audio issues and added an audio engine selector so you can choose what works best for your system (pyaudio and sounddevice)
- Small fixes

### 1.2.0
- Expanded controller support for "guitar" assets
- Added mouse tracking for drawing artists
- Added an animation selector for idle and talking
- Fixed some path issues for shortcuts

### 1.1.0

- Added controller support for "wheels" and "controllers" assets
- Fixed some path issues for the viewer
- Fixed some audio issues

### 1.0.0
 - Release Version
