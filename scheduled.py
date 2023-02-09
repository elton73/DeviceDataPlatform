'''Launch the Main Application here
'''
from modules.data_update import Update_Device, Authorization
from datetime import timedelta, date

try:
    import httplib  # python < 3.0
except:
    import http.client as httplib

def runschedule():
    start_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')  # yesterday
    end_date = date.today().strftime('%Y-%m-%d')  # today
    update = Update_Device(startDate=start_date, endDate=end_date)
    update.update_all()

if __name__ == '__main__':
    runschedule()


