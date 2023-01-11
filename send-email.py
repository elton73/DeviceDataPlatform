import modules.fitbit.authentication as auth
import modules.fitbit.retrieve as retrieve
import modules.mysql.setup as setup_db
import modules.mysql.modify as modify_db
import modules.mysql.report as report_db
from pathlib import Path
import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone, date
import pprint as pp

try:
    import httplib  # python < 3.0
except:
    import http.client as httplib
import time

from sqlalchemy import create_engine
import smtplib, ssl
import pymysql

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def sendEmail(subject, body):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "<email>"  # Enter your address
    receiver_email = ["<email>"]  # Enter receiver addresses
    password = "<enter your password>"
    message = f"Subject: {subject}\n\n{body}"

    print(message)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

def lateSyncEmail(selected_userids):
    auth_conn = sqlite3.connect(db_path)

    # Selected user IDs must be wrapped with single quotes for SQLite Query
    query_selected_userids = list(
        map(lambda text: f'\'{text}\'', selected_userids))
    access_tokens = report_db.get_auth_tokens(
        auth_conn, query_selected_userids)
    refresh_tokens = report_db.get_refresh_tokens(
        auth_conn, query_selected_userids)

    mysql_conn = create_engine(
        'mysql+pymysql://writer:password@localhost/fitbit')

    device_list = []
    request_num = 0
    start_time = time.time()
    for userid in selected_userids:

        UserDataRetriever = retrieve.DataGetter(access_tokens[userid])

        result = UserDataRetriever.get_all_devices('', '')
        if result.status_code == 401:
            # Expired token
            new_auth_info = auth.get_refreshed_auth_info(
                userid, refresh_tokens[userid])

            # Bad Refresh Token
            if new_auth_info == 400:
                print(
                    f'Bad refresh token, enter credentials for userid: {userid}')
                # new_auth_info = auth.get_auth_info()
                continue    # move on to next device

            # If There is a problem with getting new auth info, skip
            if new_auth_info == '':
                print(f'X {userid} ERROR: Could not get Access Token')
                continue    # move on to next device

            # Update the database
            modify_db.update_auth_token(
                auth_conn, userid, new_auth_info['access_token'])
            modify_db.update_refresh_token(
                auth_conn, userid, new_auth_info['refresh_token'])
            # Update the retriever
            UserDataRetriever.token = new_auth_info['access_token']
            # Try the request again

            result = UserDataRetriever.get_all_devices('', '')

        # Get the data. If intraday, it is the first date
        data = result.json()
        pp.pprint(data)

        for device in data:
            # lastSyncTime might be labeled differently for other (non-fitbit) devices
            ts = datetime.strptime(device['lastSyncTime'], "%Y-%m-%dT%H:%M:%S.%f")

            if device['deviceVersion'] not in ['Charge 2', 'Versa 3']:    
                continue  # filter out other/older fitbit devices patient may have (i.e. Versa)

            # condition to send email notification: > 1 day since last sync
            if ts + timedelta(days=4) < datetime.now():
                cursor = mysql_conn.raw_connection().cursor()
                cursor.execute(f'SELECT patientid FROM patientid WHERE userid = \'{userid}\';')

                patientid = cursor.fetchall()[0][0]
                device_list.append((patientid, device['deviceVersion']))
        
    # NOTE: Have to edit subject & body if using devices other than the Charge 2
    subject = f"[AUTOMATED] Patients haven't synced their Charge 2 for more than 3 days"
    body = f"Here is a list of patients and their out-of-sync devices: {device_list}"
    if device_list:
        sendEmail(subject, body)

    print(f'Time Elapsed for {request_num} requests = {time.time()-start_time}')

if __name__=="__main__":
    if getattr(sys, 'frozen', False):
        APPLICATION_PATH = Path(os.path.dirname(sys.executable))
    elif os.path.abspath(''):
        APPLICATION_PATH = Path(os.path.abspath(''))

    db_path = APPLICATION_PATH.joinpath('db.sqlite3')

    # Initial Setup
    if not os.path.exists(db_path):
        setup_db.create_db(APPLICATION_PATH)

    # fitbit users to monitor
    selected_userids = ['B7L3JZ', '4YGW8L']

    lateSyncEmail(selected_userids)