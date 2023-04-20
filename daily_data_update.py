'''Update all devices here daily. Check last sync time daily.
'''
from modules.data_update import Update_Device
from modules.send_email import check_last_sync
from datetime import timedelta, date
import pathlib
import time
from modules.mysql.setup import connect_to_database
from modules.mysql.modify import purge_unused_keys
from modules import LOGIN_DATABASE

try:
    import httplib  # python < 3.0
except:
    import http.client as httplib

def dailyschedule():
    path = pathlib.Path(__file__).parent.resolve()
    start_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')  # yesterday
    end_date = date.today().strftime('%Y-%m-%d')  # today
    update = Update_Device(startDate=start_date, endDate=end_date, path=path)
    update.update_all()
    fitbit_users = update.get_fitbit_users()
    if fitbit_users:
        check_last_sync(fitbit_users)



if __name__ == '__main__':
    while True:
        if time.localtime().tm_hour == 9 and time.localtime().tm_min == 0 and time.localtime().tm_sec == 0:
            print("Updating:")
            dailyschedule()
            with connect_to_database(LOGIN_DATABASE) as login_db:
                purge_unused_keys(login_db)
            time.sleep(60)