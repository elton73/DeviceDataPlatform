'''Update all devices here daily. Check last sync time daily.
'''
from modules.data_update import Update_Device
from modules.send_email import check_last_sync
from datetime import timedelta, date
import pathlib
import time

try:
    import httplib  # python < 3.0
except:
    import http.client as httplib

def runschedule():
    path = pathlib.Path(__file__).parent.resolve()
    start_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')  # yesterday
    end_date = date.today().strftime('%Y-%m-%d')  # today
    update = Update_Device(startDate=start_date, endDate=end_date, path=path)
    return update.update_all()



if __name__ == '__main__':
    while True:
        if time.localtime().tm_hour == 8 and time.localtime().tm_min == 45 and time.localtime().tm_sec == 0:
            print("Updating:")
            fitbit_users = runschedule()
            if fitbit_users:
                check_last_sync(fitbit_users)
            time.sleep(60)
