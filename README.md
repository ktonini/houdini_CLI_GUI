# houdini_CLI_GUI
Houdini GUI CLI render submitter (local)

### Requirements:
* python3
* PySimpleGUI >= 4.61.0.156
* houdini
* redshift

### Known Issues:
* Kill button kills the app as well instead of only the thread

### To Do:
* Add 'increment' integer field - default to 1
* Add 'skip existing' checkbox
* checkbox for overwriting files
* grab recent hip files from /path/to/houdiniXX.X/file.history
* get out path from hip and place ROPS in dropdown
* nth frame override
* exr (and channels) preview
* skip already rendered frames checkbox
* fix: right now if canceled before frame render, user gets message that it will be canceled, but never that it was right away
* open output folder from UI
* remember settings for window size, output view toggle, ...?
* resize output text with command + and command -
