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
    update.update_all()

    if update.check_fitbit_last_sync():
        print("Checking Last Fitbit Sync:")
        check_last_sync()

if __name__ == '__main__':
    while True:
        if time.localtime().tm_hour == 10 and time.localtime().tm_min == 2 and time.localtime().tm_sec == 0:
            print("Updating:")
            runschedule()
            time.sleep(60)
