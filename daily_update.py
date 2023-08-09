"""
Daily updates for the database at 12:00 AM
"""

from modules.update_handler import dailyschedule
import time
from modules.mysql.setup import connect_to_database
from modules import LOGIN_DATABASE
from modules.mysql.modify import purge_unused_keys

if __name__ == '__main__':
    while True:
        if time.localtime().tm_hour == 0 and time.localtime().tm_min == 0 and time.localtime().tm_sec == 0:
            print("\n", "Updating:")
            dailyschedule()
            with connect_to_database(LOGIN_DATABASE) as login_db:
                purge_unused_keys(login_db)
            time.sleep(300)