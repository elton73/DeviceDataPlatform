'''Launch the Main Application here
'''
import modules.gui.pyqtapp as gui_pyqtapp
import modules.sqlite.setup as setup_db
import modules.sqlite.modify as modify_db
import modules.sqlite.report as report_db
from pathlib import Path
import sys
import os
import sqlite3
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
    if getattr(sys, 'frozen', False):
        APPLICATION_PATH = Path(os.path.dirname(sys.executable))
    elif __file__:
        APPLICATION_PATH = Path(os.path.dirname(__file__))
    
    # Make the Data Folder if it isn't already there
    APPLICATION_PATH.joinpath('exported data').mkdir(parents=True, exist_ok=True)

    db_path = APPLICATION_PATH.joinpath('db.sqlite3')

    # Initial Setup
    if not os.path.exists(db_path):
        setup_db.create_db(APPLICATION_PATH)

    # Start the app
    # print(resource_path('resources'))
    gui_pyqtapp.run(resource_path('resources'), db_path)
