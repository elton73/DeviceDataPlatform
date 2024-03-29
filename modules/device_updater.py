"""
User and update class
"""

from modules.mysql.setup import connect_to_database
import modules.mysql.report as report_db
import requests
from sqlalchemy import create_engine
from modules import AUTH_DATABASE, POLAR_DATABASE, FITBIT_DATABASE, WITHINGS_DATABASE, USER, PASSWORD
from datetime import date
from time import time
import uuid
import os
from modules.fitbit.update import Fitbit_Update
from modules.polar.update import Polar_Update
from modules.withings.update import Withings_Update

#  User class with auth info
class User(object):
    def __init__(self, user_id):
        self.user_id = user_id
        with connect_to_database(AUTH_DATABASE) as auth_db:
            self.device_type = report_db.get_data(auth_db, user_id, 'device_type')
            self.access_token = report_db.get_data(auth_db, user_id, 'auth_token')
            self.refresh_token = report_db.get_data(auth_db, user_id, 'refresh_token')
            self.patient_id = report_db.get_data(auth_db, user_id, 'patient_id')

    """
    FITBIT API
    """
    def get_refreshed_fitbit_auth_info(self):
        CLIENT_ID = os.environ.get('FITBIT_CLIENT_ID')
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': CLIENT_ID,
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        token_exchange_url = f'https://api.fitbit.com/oauth2/token'
        result = requests.post(token_exchange_url, headers=headers, data=payload)
        if result.status_code == 400:
            # Handling of bad refresh token
            print(f'Bad refresh token, enter credentials for userid: {self.user_id}')
            return 400
        else:
            return result.json()

    """
    Withings API
    """
    def get_refreshed_withings_auth_info(self):
        CLIENT_ID = os.environ.get('WITHINGS_CLIENT_ID')
        CLIENT_SECRET = os.environ.get('WITHINGS_CLIENT_SECRET')
        payload = {
            'action': 'requesttoken',
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        token_exchange_url = f'https://wbsapi.withings.net/v2/oauth2'
        result = requests.post(token_exchange_url, headers=headers, data=payload)
        if result.status_code == 400:
            # Handling of bad refresh token
            print(f'Bad refresh token, enter credentials for userid: {self.user_id}')
            return 400
        else:
            return result.json()

    """
    Polar API
    """
    def check_polar_member_id(self):
        command = f'''
            SELECT member_id FROM member_ids WHERE userid = {self.user_id}
            '''
        with connect_to_database(POLAR_DATABASE) as db:
            cursor = db.cursor()
            cursor.execute(command)
            #check if member_id already exists
            member_id = cursor.fetchone()[0]
            if not member_id:
                member_id = self.register_polar_user(db)
            return member_id

    # Register user and upload member_id to mysql
    def register_polar_user(self, db):
        cursor = db.cursor()

        #Check if member_id already exists
        check_for_id = True
        while check_for_id:
            member_id = uuid.uuid4().hex
            command = f"SELECT member_id FROM member_ids WHERE member_id = '{member_id}'"
            cursor.execute(command)
            check_for_id = cursor.fetchone()
            check_for_id = check_for_id[0] if check_for_id else check_for_id

        result = requests.post('https://www.polaraccesslink.com/v3/users', headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'},
                               json={"member-id": member_id},
                               )
        # if unsuccessful post
        if result.status_code != 200:
            print(f"Couldn't Register User. Status code: {result.status_code}")
            return False
        command = f"UPDATE member_ids SET member_id = '{member_id}' WHERE userid = '{self.user_id}'"
        cursor.execute(command)
        db.commit()
        return member_id

#  Update class to update all devices
class Update_Device(object):
    def __init__(self, startDate, endDate, path):
        self.startDate = startDate
        self.endDate = endDate
        self.request_num = 0
        self.users = self.generate_users()

        self.users_updated = []

        self.users_skipped = []
        self.path = path

        self.out_of_sync_fitbits = []

        self.FITBIT_ENGINE = create_engine(f'mysql+pymysql://{USER}:{PASSWORD}@localhost/{FITBIT_DATABASE}')
        self.WITHINGS_ENGINE = create_engine(f'mysql+pymysql://{USER}:{PASSWORD}@localhost/{WITHINGS_DATABASE}')
        self.POLAR_ENGINE = create_engine(f'mysql+pymysql://{USER}:{PASSWORD}@localhost/{POLAR_DATABASE}')

    #update all devices
    def update_all(self, user_id=None):
        #no users
        start = time()
        if not self.users:
            print("No users")
            return self.request_num

        #  filter out users when updating a single user
        for user in self.users:
            if user_id and user.user_id != user_id:
                continue

            #  Skip user if their data has been already updated. Polar users do not use this
            if self.already_updated(user):
                continue

            # fitbit api
            if user.device_type == 'fitbit':
                updater = Fitbit_Update(user, self.startDate, self.endDate, self.path, self.FITBIT_ENGINE)

                # When doing a manual update, do not check fitbit sync times.
                if user_id:
                    updater.is_manual_update = True

                #  flag for if the user was successfully updated
                flag = updater.update()
                if flag:
                    self.users_updated.append(user.user_id)
                    self.request_num += 1
                else:
                    self.users_skipped.append(user.user_id)

                #  get a list of users who haven't synced their fitbit for more than 3 days
                if updater.send_email:
                    self.out_of_sync_fitbits.append(user)

            # withings api
            elif user.device_type == "withings":
                updater = Withings_Update(user, self.startDate, self.endDate, self.path, self.WITHINGS_ENGINE)
                flag = updater.update()
                if flag:
                    self.users_updated.append(user.user_id)
                    self.request_num += 1
                else:
                    self.users_skipped.append(user.user_id)

            # polar api
            elif user.device_type == "polar":
                updater = Polar_Update(user, self.startDate, self.endDate, self.path, self.POLAR_ENGINE)
                flag = updater.update()
                if flag:
                    self.users_updated.append(user.user_id)
                    self.request_num += 1
                else:
                    self.users_skipped.append(user.user_id)

        self.FITBIT_ENGINE.dispose()
        self.WITHINGS_ENGINE.dispose()
        self.POLAR_ENGINE.dispose()

        print(f"Users updated: {self.users_updated}")
        print(f"Users skipped: {self.users_skipped}")
        print(f"{self.request_num} users updated in {time() - start} seconds on {date.today()}")
        return self.request_num

    #generate list of all users in auth database
    def generate_users(self):
        users = set()
        with connect_to_database(AUTH_DATABASE) as db:
            for userid in report_db.get_all_user_ids(db):
                user = User(user_id=userid)
                users.add(user)
        return users

    #check if device was updated today
    def already_updated(self, user):
        if user.device_type == "fitbit":
            db_name = FITBIT_DATABASE
        elif user.device_type == "withings":
            db_name = WITHINGS_DATABASE
        #Polar checks for duplicate data differently
        else:
            return False
        with connect_to_database(db_name) as db:
            cursor = db.cursor()
            try:
                command = f"SELECT * FROM devices WHERE userid = '{user.user_id}' AND lastUpdate = '{self.endDate}'"
                cursor.execute(command)
                if cursor.fetchone():
                    self.users_skipped.append(user.user_id)
                    #debug
                    print(f"User {user.user_id} is updated to today.")
                    return True
                return False
            except Exception as e:
                print(e)
                return False

