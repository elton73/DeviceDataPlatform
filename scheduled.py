'''Update All Devices Here. Used with task scheduler.
'''
from modules.data_update import Update_Device
from datetime import timedelta, date
import pathlib

try:
    import httplib  # python < 3.0
except:
    import http.client as httplib

def runschedule():
    path = pathlib.Path(__file__).parent.resolve()
    #get data for a specific day
    # start_date = (date.today() - timedelta(days=3)).strftime('%Y-%m-%d')  # yesterday
    # end_date = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d')  # yesterday

    start_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')  # yesterday
    end_date = date.today().strftime('%Y-%m-%d')  # today
    update = Update_Device(startDate=start_date, endDate=end_date, path=path)
    return update.update_all()

if __name__ == '__main__':
    runschedule()



