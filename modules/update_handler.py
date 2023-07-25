'''
Methods for updating the database
'''
from modules.device_updater import Update_Device
from modules.email_handler import lateSyncEmail
from datetime import timedelta, date
import pathlib

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
    if update.out_of_sync_fitbits:
        lateSyncEmail(update.out_of_sync_fitbits)

def web_app_update():
    path = pathlib.Path(__file__).parent.resolve()
    start_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')  # yesterday
    end_date = date.today().strftime('%Y-%m-%d')  # today
    update = Update_Device(startDate=start_date, endDate=end_date, path=path)
    return update.update_all()

def manualschedule(days, user_id):
   path = pathlib.Path(__file__).parent.resolve()
   start_date = (date.today() - timedelta(days=days)).strftime('%Y-%m-%d')
   end_date = (date.today() - timedelta(days=(days-1))).strftime('%Y-%m-%d')
   update = Update_Device(startDate=start_date, endDate=end_date, path=path)
   update.update_all(user_id)

