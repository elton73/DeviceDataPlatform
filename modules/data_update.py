import modules.fitbit.retrieve as fitbit_retrieve
import modules.withings.retrieve as withings_retrieve
from modules.mysql.setup import connect_to_database
import modules.mysql.modify as modify_db
import modules.mysql.report as report_db
import requests
import pandas as pd
from datetime import datetime, timedelta, date
from modules import AUTH_DATABASE, FITBIT_ENGINE, WITHINGS_ENGINE, FITBIT_TABLES, WITHINGS_TABLES, WITHINGS_COLUMNS
from time import time

AUTH_DB = connect_to_database(AUTH_DATABASE)

class  Authorization(object):
    def __init__(self, userid):
        self.userid = userid
        self.device_type = report_db.get_data(AUTH_DB, userid, 'device_type')
        self.access_token = report_db.get_data(AUTH_DB, userid, 'auth_token')
        self.refresh_token = report_db.get_data(AUTH_DB, userid, 'refresh_token')

    def get_refreshed_fitbit_auth_info(self):
        CLIENT_ID = "23BHY7"# who's client id is this?
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
            print(f'Bad refresh token, enter credentials for userid: {self.userid}')
            return 400
        else:
            return result.json()

    def get_refreshed_withings_auth_info(self):
        CLIENT_ID = "d96eba460244559633e00680cddde41a26a13ebc0dc79a579cc94821479453f5"
        CLIENT_SECRET = "b6d749ee51bcb761afd8b0ca02d16cdd148fd39e2e03eac05334465e85f04d25"
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
            print(f'Bad refresh token, enter credentials for userid: {self.userid}')
            return 400
        else:
            return result.json()


class Update_Device(object):
    def __init__(self, startDate, endDate):
        self.startDate = startDate
        self.endDate = endDate
        self.request_num = 0
        self.users = self.generate_users()

    def update_all(self):
        #no users
        start = time()
        if not self.users:
            print("No users")
            return False
        for user in self.users:
            if user.device_type == 'fitbit':
                self.update_fitbit(user)
                self.request_num += 1
            if user.device_type == "withings":
                self.update_withings(user)
                self.request_num += 1

        return print(f"{self.request_num} users updated in {time()-start} seconds")

    def update_withings(self, user):
        UserDataRetriever = withings_retrieve.DataGetter(user.access_token)
        device_data = []
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
                modify_db.update_auth_token(AUTH_DB, user.userid, new_auth_info['access_token'])
                modify_db.update_refresh_token(AUTH_DB, user.userid, new_auth_info['refresh_token'])
                # Update the retriever
                UserDataRetriever.token = new_auth_info['access_token']
                raw_data = UserDataRetriever.api_map[data_value](self.startDate, self.endDate).json()
            data = raw_data['body']['series']
            if len(data):
                #df.to_sql needs a very specific data structure so we reformat our data
                formatted_data = self.format_withings_data(data, data_key)
                df = pd.DataFrame(formatted_data)
                df['userid'] = user.userid
                table = data_value.replace('-', '').replace(' dataset', '')
                df.to_sql(con=WITHINGS_ENGINE, name=table, if_exists='append')
            # Manually update device data to mysql
            if not device_data:
                device_data = [{
                    'model': data[0][f'model']
                }]
                # print(device_data)
                device_df = pd.DataFrame(device_data)
                device_df['userid'] = user.userid
                device_df.to_sql(con=WITHINGS_ENGINE, name="devices", if_exists='append')


    def update_fitbit(self, user):
        UserDataRetriever = fitbit_retrieve.DataGetter(user.access_token)

        for data_key, data_value in FITBIT_TABLES.items():
            result = UserDataRetriever.api_map[data_key](self.startDate, self.endDate)
            # Expired token
            if result.status_code == 401:
                new_auth_info = user.get_refreshed_fitbit_auth_info()
                # If There is a problem with getting new auth info, skip
                if new_auth_info == '':
                    break
                # Update the database
                modify_db.update_auth_token(AUTH_DB, user.userid, new_auth_info['access_token'])
                modify_db.update_refresh_token(AUTH_DB, user.userid, new_auth_info['refresh_token'])
                # Update the retriever
                UserDataRetriever.token = new_auth_info['access_token']
            data = result.json()

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
                data = [flatten_dictionary(d) for d in data]
                df = pd.DataFrame(data)
                df['userid'] = user.userid

                table = data_value
                print(table)
                # try:
                #     df.to_sql(con=FITBIT_ENGINE, name=table, if_exists='append')
                # except:
                #     continue

   #Control how the Withings data is structured. This changes how the information will look on mysql
    def format_withings_data(self, data, data_key):
        time = []
        index = 0
        for dict in data:
            time.append({})
            #search the dictionary by key for the data we want
            data_dict = dict[f'{data_key}']
            # Different data has different formats, so we format data accordingly
            if "data" not in dict:
                for k,v in data_dict.items():
                    time[index]['time']= datetime.fromtimestamp(int(k))
                    time[index]['value']= v
            else:
                for k, v in data_dict.items():
                    time[index]['sleep_start']= datetime.fromtimestamp(int(dict['startdate']))
                    time[index]['sleep_end'] = datetime.fromtimestamp(int(dict['enddate']))
                    if k == "total_sleep_time" or k == "waso":
                        #convert seconds to minutes
                        v = round(v/60)
                    time[index][f'{WITHINGS_COLUMNS[k]}']= v

            index += 1


        return time

    def pop_data(self, keys, dict):
        for key in keys:
            if key in dict:
                dict.pop(key)
        return dict
    def generate_users(self):
        users = set()
        for userid in report_db.get_all_user_ids(AUTH_DB):
            user = Authorization(userid=userid)
            users.add(user)
        return users

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
    end_date = date.today().strftime('%Y-%m-%d')  # today
    update = Update_Device(startDate=start_date, endDate=end_date)
    update.update_all()
