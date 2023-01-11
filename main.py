'''Launch the Main Application here
'''
import sys
import os
import modules.gui.pyqtapp as gui_pyqtapp
from pathlib import Path
from datetime import datetime, timedelta, timezone
import json

# https://stackoverflow.com/questions/59966120/how-to-add-statichtml-css-js-etc-files-in-pyinstaller-to-create-standalone
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


if __name__ == '__main__':

    # Start the app
    # print(resource_path('resources'))

    gui_pyqtapp.run(resource_path('resources'))
    
    
