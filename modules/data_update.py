import modules.fitbit.retrieve as fitbit_retrieve
import modules.withings.retrieve as withings_retrieve
import modules.polar.retrieve as polar_retrieve
from modules.mysql.setup import connect_to_database
import modules.mysql.modify as modify_db
import modules.mysql.report as report_db
import requests
import pandas as pd
from datetime import datetime, timedelta, date
from modules import AUTH_DATABASE, FITBIT_ENGINE, WITHINGS_ENGINE, FITBIT_TABLES, WITHINGS_TABLES, \
    WITHINGS_COLUMNS, POLAR_DATABASE, POLAR_TABLES, POLAR_ENGINE, FITBIT_DATABASE, WITHINGS_DATABASE
from time import time
import uuid
import os

class Authorization(object):
    def __init__(self, user_id):
        self.db = connect_to_database(AUTH_DATABASE)
        self.user_id = user_id
        self.device_type = report_db.get_data(self.db, user_id, 'device_type')
        self.access_token = report_db.get_data(self.db, user_id, 'auth_token')
        self.refresh_token = report_db.get_data(self.db, user_id, 'refresh_token')

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
        db = connect_to_database(POLAR_DATABASE)
        command = f'''
            SELECT member_id FROM member_ids WHERE userid = {self.user_id}
            '''
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
            cursor.execute(f"SELECT member_id FROM member_ids WHERE member_id = '{member_id}'")
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

        cursor.execute(f"UPDATE member_ids SET member_id = '{member_id}' WHERE userid = '{self.user_id}'")
        db.commit()
        return member_id

class Update_Device(object):
    def __init__(self, startDate, endDate):
        self.startDate = startDate
        self.endDate = endDate
        self.request_num = 0
        self.users = self.generate_users()
        self.users_updated = []
        self.users_skipped = []

    #update all devices
    def update_all(self):
        #no users
        start = time()
        if not self.users:
            print("No users")
            return self.request_num

        for user in self.users:
            print(user.user_id)
            """
            Skip user if their data has been already updated. Polar does not use this check.
            """
            if self.already_updated(user):
                continue
            if user.device_type == 'fitbit':
                self.update_fitbit(user)
            elif user.device_type == "withings":
                self.update_withings(user)
            elif user.device_type == "polar":
                self.update_polar(user)

        print(f"Users updated: {self.users_updated}")
        print(f"User skipped: {self.users_skipped}")
        print(f"{self.request_num} users updated in {time() - start} seconds")
        return self.request_num

    """
    Polar API
    """
    def update_polar(self, user):
        member_id = user.check_polar_member_id()
        data_flag = False #Flag for if user has data to be uploaded to mysql
        UserDataRetriever = polar_retrieve.DataGetter(user.access_token, user.user_id)
        for data_key, data_value in POLAR_TABLES.items():
            data = UserDataRetriever.api_map[data_value]()
            if not data:
                break
            else:
                data_flag = True
            #format data
            if data_key == 'exercise_summary':
                formatted_data = self.format_exercise_summary(data, user.user_id)
            elif data_key == 'heart_rate':
                formatted_data = self.format_heart_rate(data, user.user_id)
            df = pd.DataFrame(formatted_data)
            table = data_value.replace('-', '').replace(' dataset', '')
            df.to_sql(con=POLAR_ENGINE, name=table, if_exists='append')
            #commit transaction. Old data will be deleted
            UserDataRetriever.commit_transaction()
        if data_flag:
            self.users_updated.append(user.user_id)
            self.request_num += 1
            return True
        else:
            self.users_skipped.append(user.user_id)
            return False

    #Format polar_data
    def format_exercise_summary(self, data, user_id):
        for exercise_summary in data:
            #remove data columns
            pop_columns = ['upload-time', 'polar-user', 'transaction-id', 'start-time-utc-offset', 'has-route',
                           'detailed-sport-info']
            for column in pop_columns:
                exercise_summary.pop(column)

            heart_rate = exercise_summary.pop('heart-rate')
            exercise_summary['start_time'] = exercise_summary.pop('start-time')
            exercise_summary['hr_average'] = heart_rate['average']
            exercise_summary['hr_max'] = heart_rate['maximum']
            exercise_summary['userid'] = user_id
        return data

    def format_heart_rate(self, data, user_id):
        output = []
        index = 0
        for heart_rates in data:
            id = heart_rates['id']

            #format our own time since polar doesn't provide it
            db = connect_to_database(POLAR_DATABASE)
            cursor = db.cursor()
            cursor.execute(f"SELECT start_time FROM exercise_summary WHERE id='{id}'")
            raw_time = cursor.fetchone()
            formatted_time = raw_time[0].replace("T", " ") if raw_time else raw_time
            current_time = datetime.strptime(formatted_time, "%Y-%m-%d %H:%M:%S")

            #create rows
            recording_rate = heart_rates['recording-rate']
            for heart_rate in heart_rates['data'].split(","):
                output.append({})
                output[index]['id'] = id
                output[index]['time'] = current_time
                output[index]['value'] = int(heart_rate)
                output[index]['userid'] = user_id
                index += 1
                current_time = current_time + timedelta(seconds=recording_rate)
        return output

    """
    Withings API
    """
    def update_withings(self, user):
        UserDataRetriever = withings_retrieve.DataGetter(user.access_token)
        device_data = []
        data_flag = False  # Flag for if user has data to be uploaded to mysql
        for data_key, data_value in WITHINGS_TABLES.items():
            result = UserDataRetriever.api_map[data_value](self.startDate, self.endDate)
            raw_data = result.json()
            #error codes
            if str(raw_data['status']) == '401':
                new_auth_info = user.get_refreshed_withings_auth_info()['body']
                if str(new_auth_info) == '400':
                    break
                if new_auth_info == '':
                    break
                # Update the database
                modify_db.update_auth_token(user.db, user.user_id, new_auth_info['access_token'])
                modify_db.update_refresh_token(user.db, user.user_id, new_auth_info['refresh_token'])
                # Update the retriever
                UserDataRetriever.token = new_auth_info['access_token']
                raw_data = UserDataRetriever.api_map[data_value](self.startDate, self.endDate).json()
            data = raw_data['body']['series']
            #if there is no data, move on
            if not data:
                break
            else:
                data_flag += 1
            if len(data):
                # reformat data before creating dataframe
                formatted_data = self.format_withings_data(data, data_key)
                df = pd.DataFrame(formatted_data)
                df['userid'] = user.user_id
                table = data_value.replace('-', '').replace(' dataset', '')
                df.to_sql(con=WITHINGS_ENGINE, name=table, if_exists='append')
            # Manually update device data to mysql
            if not device_data:
                device_data = [{
                    'model': data[0][f'model'],
                }]
                device_df = pd.DataFrame(device_data)
                device_df['userid'] = user.user_id
                device_df['lastUpdate'] = self.endDate
                device_df.to_sql(con=WITHINGS_ENGINE, name="devices", if_exists='replace')
        if data_flag:
            self.users_updated.append(user.user_id)
            self.request_num += 1
            return True
        else:
            self.users_skipped.append(user.user_id)
            return False

    # Control how the Withings data is structured. This changes how the information will look on mysql
    def format_withings_data(self, data, data_key):
        time = []
        index = 0
        for dict in data:
            time.append({})
            # search the dictionary by key for the data we want
            data_dict = dict[f'{data_key}']
            # Different data has different formats, so we format data accordingly
            if "data" not in dict:
                for k, v in data_dict.items():
                    time[index]['time'] = datetime.fromtimestamp(int(k))
                    time[index]['value'] = v
            else:
                for k, v in data_dict.items():
                    time[index]['sleep_start'] = datetime.fromtimestamp(int(dict['startdate']))
                    time[index]['sleep_end'] = datetime.fromtimestamp(int(dict['enddate']))
                    if k == "total_sleep_time" or k == "waso":
                        # convert seconds to minutes
                        v = round(v / 60)
                    time[index][f'{WITHINGS_COLUMNS[k]}'] = v
            index += 1
        return time

    """
    Fitbit API
    """
    def update_fitbit(self, user):
        UserDataRetriever = fitbit_retrieve.DataGetter(user.access_token)
        data_flag = False  # Flag for if user has data to be uploaded to mysql
        for data_key, data_value in FITBIT_TABLES.items():
            result = UserDataRetriever.api_map[data_key](self.startDate, self.endDate)
            # Expired token
            if result.status_code == 401:
                new_auth_info = user.get_refreshed_fitbit_auth_info()
                # If There is a problem with getting new auth info, skip
                if new_auth_info == '':
                    break
                # Update the database
                modify_db.update_auth_token(user.db, user.user_id, new_auth_info['access_token'])
                modify_db.update_refresh_token(user.db, user.user_id, new_auth_info['refresh_token'])
                # Update the retriever
                UserDataRetriever.token = new_auth_info['access_token']
            data = result.json()
            #break if there is no device
            if data_key == "devices" and data == []:
                break
            if type(data) is dict:
                if 'errors' in list(data.keys()):
                    errorFlag = True
                    break

                # Get the first list
                for key in data_key.split(' '):
                    data = data[key]

                # Handle Intraday - selection includes 'dataset'... since intraday can only grab one day
                if len(data_key.split(' ')) > 1 and data_key.split(' ')[1] == 'dataset':
                    data = []
                    intraday_dates = list(range_dates(datetime.strptime(self.startDate, '%Y-%m-%d').date(),
                                                      datetime.strptime(self.endDate, '%Y-%m-%d').date()))
                    for one_date in intraday_dates:
                        # Grab the result for the next date
                        result = UserDataRetriever.api_map[data_key](str(one_date),
                                                                     self.endDate)  # Since one_date is a datetime.date
                        next_day_data = result.json()

                        # Fitbit only returns the time so format it into a datetime

                        for key in data_key.split(' '):
                            next_day_data = next_day_data[key]
                        # Format time to datetime
                        next_day_data = [
                            {'datetime': datetime.strptime(f"{str(one_date)} {data['time']}", "%Y-%m-%d %H:%M:%S"),
                             'value': data['value']} for data in next_day_data]
                        # There should only be a list left
                        data += next_day_data
            if len(data):
                data_flag = True
                data = [flatten_dictionary(d) for d in data]
                df = pd.DataFrame(data)
                df['userid'] = user.user_id
                table = data_value

                #Don't append for devices table
                try:
                    if table == "devices":
                        df['lastUpdate'] = self.endDate
                        df.to_sql(con=FITBIT_ENGINE, name=table, if_exists='replace')
                    else:
                        df.to_sql(con=FITBIT_ENGINE, name=table, if_exists='append')
                except:
                    continue
        if data_flag:
            self.users_updated.append(user.user_id)
            self.request_num += 1
            return True
        else:
            self.users_skipped.append(user.user_id)
            return False
    def pop_data(self, keys, dict):
        for key in keys:
            if key in dict:
                dict.pop(key)
        return dict
    def generate_users(self):
        users = set()
        db = connect_to_database(AUTH_DATABASE)
        for userid in report_db.get_all_user_ids(db):
            user = Authorization(user_id=userid)
            users.add(user)
        return users

    def already_updated(self, user):
        if user.device_type == "fitbit":
            db = connect_to_database(FITBIT_DATABASE)
        elif user.device_type == "withings":
            db = connect_to_database(WITHINGS_DATABASE)
        #Polar won't have duplicate data
        else:
            return False
        cursor = db.cursor()
        try:
            cursor.execute(f"SELECT * FROM devices WHERE userid = '{user.user_id}' AND lastUpdate = '{self.endDate}'")
            if cursor.fetchone():
                self.users_skipped.append(user.user_id)
                return True
            return False
        except Exception as e:
            print(e)
            return False


def range_dates(startDate, endDate, step=1):
    for i in range((endDate - startDate).days):
        yield startDate + timedelta(days=step * i)

def flatten_dictionary(some_dict, parent_key='', separator='_'):
    flat_dict = {}
    for k, v in some_dict.items():
        new_key = parent_key + separator + k if parent_key else k
        new_key = new_key.replace(' ', '')
        if isinstance(v, list):
            continue # v = dict([(x['name'], x) for x in v])
        if isinstance(v, dict):
            flat_dict.update(flatten_dictionary(v, parent_key=new_key))
        else:
            flat_dict[new_key] = v
    return flat_dict



if __name__ == '__main__':
    start_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')  # yesterday
    end_date = date.today().strftime('%Y-%m-%d')  # today %Y-%m-%d
    update = Update_Device(startDate=start_date, endDate=end_date)
    update.update_all()

