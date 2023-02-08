import modules.fitbit.retrieve as fitbit_retrieve
import modules.withings.retrieve as withings_retrieve
from modules.mysql.setup import connect_to_database
import modules.mysql.modify as modify_db
import modules.mysql.report as report_db
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone, date
from modules import AUTH_DATABASE, FITBIT_ENGINE, WITHINGS_ENGINE

FITBIT_DATATYPES = ['devices', 'activities-steps', 'sleep', 'activities-heart-intraday dataset',
                          'activities-steps-intraday dataset']
WITHINGS_DATATYPES = {'hr': 'heart_rate', 'rr': 'respiration_rate', 'snoring': 'snoring_time'}
AUTH_DB = connect_to_database(AUTH_DATABASE)

class  Authorization(object):
    def __init__(self, userid):
        self.userid = userid
        self.device_type = report_db.get_data(AUTH_DB, userid, 'device_type')
        self.access_token = report_db.get_data(AUTH_DB, userid, 'auth_token')
        self.refresh_token = report_db.get_data(AUTH_DB, userid, 'refresh_token')

    def get_refreshed_fitbit_auth_info(self):
        CLIENT_ID = "23BHY7"
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


class Update_Device(object):
    def __init__(self, startDate, endDate, request_num):
        self.startDate = startDate
        self.endDate = endDate
        self.request_num = request_num
        self.users = self.generate_users()

    def increment_request_num(self):
        self.request_num += 1
        return self.request_num

    def generate_users(self):
        users = set()
        for userid in report_db.get_all_user_ids(AUTH_DB):
            user = Authorization(userid=userid)
            users.add(user)
        return users

    def update_all(self):
        #no users
        if not self.users:
            print("No users")
            return False

        for user in self.users:
            # if user.device_type == 'fitbit':
            #     self.update_fitbit(user)
            if user.device_type == "withings":
                self.update_withings(user)
        return True

    def update_withings(self, user):
        UserDataRetriever = withings_retrieve.DataGetter(user.access_token)
        for data_key, data_value in WITHINGS_DATATYPES.items():
            result = UserDataRetriever.api_map[data_value](self.startDate, self.endDate)
            raw_data = result.json()
            data = raw_data['body']['series']
            self.request_num += 1
            if len(data):
                formatted_data = self.format_withings_data(data, data_key)
                df = pd.DataFrame(formatted_data)
                df['userid'] = user.userid
                table = data_value.replace('-', '').replace(' dataset', '')
                df.to_sql(con=WITHINGS_ENGINE, name=table, if_exists='append')



    def update_fitbit(self, user):
        UserDataRetriever = fitbit_retrieve.DataGetter(user.access_token)

        for dataType in FITBIT_DATATYPES:
            result = UserDataRetriever.api_map[dataType.keys()](self.startDate, self.endDate)
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
            self.request_num += 1

            if type(data) is dict:
                if 'errors' in list(data.keys()):
                    errorFlag = True
                    break

                # Get the first list
                for key in dataType.split(' '):
                    data = data[key]

                # Handle Intraday - selection includes 'dataset'... since intraday can only grab one day
                if len(dataType.split(' ')) > 1 and dataType.split(' ')[1] == 'dataset':
                    data = []
                    intraday_dates = list(range_dates(datetime.strptime(self.startDate, '%Y-%m-%d').date(),
                                                      datetime.strptime(self.endDate, '%Y-%m-%d').date()))
                    for one_date in intraday_dates:
                        # Grab the result for the next date
                        result = UserDataRetriever.api_map[dataType](str(one_date),
                                                                     self.endDate)  # Since one_date is a datetime.date
                        next_day_data = result.json()

                        # Fitbit only returns the time so format it into a datetime

                        for key in dataType.split(' '):
                            next_day_data = next_day_data[key]
                        # Format time to datetime
                        next_day_data = [
                            {'datetime': datetime.strptime(f"{str(one_date)} {data['time']}", "%Y-%m-%d %H:%M:%S"),
                             'value': data['value']} for data in next_day_data]
                        # There should only be a list left
                        data += next_day_data
                        self.request_num += 1
            if len(data):
                data = [flatten_dictionary(d) for d in data]
                print(data)
                df = pd.DataFrame(data)
                df['userid'] = user.userid
                table = dataType.replace('-', '').replace(' dataset', '')
                try:
                    df.to_sql(con=FITBIT_ENGINE, name=table, if_exists='append')
                except:
                    continue
    def format_withings_data(self, data, data_key):
        time = []
        for d in data:
            d.pop('startdate')
            d.pop('state')
            d.pop('enddate')
            d.pop('hash_deviceid')
            d.pop('model_id')
            h = d[f'{data_key}']
            for k,v in h.items():
                time.append({
                    'time': datetime.fromtimestamp(int(k)),
                    'value': v
                })
        return time
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
    update = Update_Device(startDate=start_date, endDate=end_date, request_num=0)
    update.update_all()
