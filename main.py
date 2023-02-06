'''Launch the Main Application here
'''
import modules.gui.pyqtapp as gui_pyqtapp
import modules.mysql.setup as setup_db
from modules.main_app.setup import create_data_folder, resource_path
from modules import DEVICE_DATABASE

if __name__ == '__main__':

    # Create an 'exported data' folder if it does not exist
    create_data_folder()

    #Connect to the database
    db = setup_db.connect_to_database(DEVICE_DATABASE)

    # Start the app
    gui_pyqtapp.run(resource_path('resources'), db)