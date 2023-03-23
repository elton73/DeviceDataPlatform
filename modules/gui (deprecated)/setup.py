import sys
import os
from pathlib import Path

# https://stackoverflow.com/questions/59966120/how-to-add-statichtml-css-js-etc-files-in-pyinstaller-to-create-standalone
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("../main_app")
    return os.path.join(base_path, relative_path)

def create_data_folder():
    if getattr(sys, 'frozen', False):
        APPLICATION_PATH = Path(os.path.dirname(sys.executable))
    elif __file__:
        APPLICATION_PATH = Path(os.path.dirname(__file__))

        # Make the Data Folder if it isn't already there
    return (APPLICATION_PATH.joinpath('exported data').mkdir(parents=True, exist_ok=True))

