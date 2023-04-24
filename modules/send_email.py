"""
Check last sync time and send email.
"""

from modules import USER, PASSWORD, FITBIT_DATABASE
import modules.fitbit.retrieve as retrieve
import modules.mysql.setup as setup_db
import modules.mysql.modify as modify_db
from modules import AUTH_DATABASE
import sys
import os
from sqlalchemy import create_engine
from datetime import datetime, timedelta

try:
    import httplib  # python < 3.0
except:
    import http.client as httplib
import time
import smtplib, ssl


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("..")

    return os.path.join(base_path, relative_path)


def sendEmail(subject, body):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = os.environ.get('DATA_PLATFORM_EMAIL')  # Enter your address
    receiver_email = ["ehlam@ualberta.ca"]
    # receiver_email = json.loads(os.environ.get('EMAIL_LIST'))  # Enter receiver addresses
    password = os.environ.get('DATA_PLATFORM_PASSWORD')
    message = f"Subject: {subject}\n\n{body}"

    print(message)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)


def lateSyncEmail(users):
    with setup_db.connect_to_database(AUTH_DATABASE) as auth_conn:
        mysql_conn = create_engine(f'mysql+pymysql://{USER}:{PASSWORD}@localhost/{FITBIT_DATABASE}')

        device_list = []
        request_num = 0
        start_time = time.time()
        for user in users:
            print(f"lateSyncEmail user: {user.user_id}")
            UserDataRetriever = retrieve.DataGetter(user.user_id)

            result = UserDataRetriever.get_all_devices('', '')
            if result.status_code == 401:
                # Expired token
                new_auth_info = user.get_refreshed_fitbit_auth_info()

                # Bad Refresh Token
                if new_auth_info == 400:
                    continue  # move on to next device

                # If There is a problem with getting new auth info, skip
                if new_auth_info == '':
                    print(f'X {user.user_id} ERROR: Could not get Access Token')
                    continue  # move on to next device

                # Update the database
                modify_db.update_auth_token(
                    auth_conn, user.user_id, new_auth_info['access_token'])
                modify_db.update_refresh_token(
                    auth_conn, user.user_id, new_auth_info['refresh_token'])
                # Update the retriever
                UserDataRetriever.token = new_auth_info['access_token']
                # Try the request again

                result = UserDataRetriever.get_all_devices('', '')

            # Get the data. If intraday, it is the first date
            data = result.json()

            for device in data:
                # lastSyncTime might be labeled differently for other (non-fitbit) devices
                ts = datetime.strptime(device['lastSyncTime'], "%Y-%m-%dT%H:%M:%S.%f")
                # condition to send email notification: > 1 day since last sync
                if ts + timedelta(days=4) < datetime.now():
                    cursor = mysql_conn.raw_connection().cursor()
                    cursor.execute(f'SELECT patient_id FROM patient_ids WHERE userid = \'{user.user_id}\';')

                    patientid = cursor.fetchall()[0][0]
                    device_list.append((patientid, device['deviceVersion']))

        # NOTE: Have to edit subject & body if using devices other than the Charge 2
        subject = f"[AUTOMATED] Patients haven't synced their Charge 2 for more than 3 days"
        body = f"Here is a list of patients and their out-of-sync devices: {device_list}"
        if device_list:
            print("Sending Email...")
            sendEmail(subject, body)

def check_last_sync(users):
    lateSyncEmail(users)

# if __name__ == '__main__':
    # check_last_sync()