'''Update All Devices Here
'''
from modules.data_update import Update_Device
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
        if time.localtime().tm_hour == 8 and time.localtime().tm_min == 0 and time.localtime().tm_sec == 0:
            runschedule()
            time.sleep(60)