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
    patient_list = []
    for user in users:
        patient_list.append(user.patient_id)
    # NOTE: Have to edit subject & body if using devices other than the Charge 2
    subject = f"[AUTOMATED] Patients haven't synced their Charge 2 for more than 3 days"
    body = f"Here is a list of patients and their out-of-sync devices: {patient_list}"
    if patient_list:
        print("Sending Email...")
        sendEmail(subject, body)
