'''Launch the Main Application here
'''
import modules.gui.pyqtapp as gui_pyqtapp
import modules.mysql.setup as setup_db
from modules.main_app.setup import create_data_folder, resource_path

if __name__ == '__main__':

    # Create an 'exported data' folder if it does not exist
    create_data_folder()

    #Connect to the database
    DATABASE = "fitbit"
    db_path = setup_db.connect_to_database(DATABASE)

    # Start the app
    gui_pyqtapp.run(resource_path('resources'), db_path)