import modules.fitbit.retrieve as fitbit_retrieve
from modules.mysql.setup import connect_to_database
import modules.mysql.modify as modify_db
import pandas as pd
from datetime import datetime, timedelta
from modules import AUTH_DATABASE, FITBIT_TABLES, FITBIT_DATABASE
import os

class Fitbit_Update():
    def __init__(self, user, startDate, endDate, filepath, engine):
        self.user = user
        self.startDate = startDate
        self.endDate = endDate
        self.data_retriever = fitbit_retrieve.DataGetter(user.access_token)
        self.engine = engine
        self.filepath = filepath

    def update(self):
        data_flag = False  # Flag for if user has data to be uploaded to mysql
        for data_key, data_value in FITBIT_TABLES.items():
            result = self.data_retriever.api_map[data_key](self.startDate, self.endDate)
            # Expired token
            if result.status_code == 401:
                new_auth_info = self.user.get_refreshed_fitbit_auth_info()
                # If There is a problem with getting new auth info, skip
                if new_auth_info == '':
                    break
                # Update the database
                with connect_to_database(AUTH_DATABASE) as auth_db:
                    modify_db.update_auth_token(auth_db, self.user.user_id, new_auth_info['access_token'])
                    modify_db.update_refresh_token(auth_db, self.user.user_id, new_auth_info['refresh_token'])
                # Update the retriever
                self.data_retriever.token = new_auth_info['access_token']
            data = result.json()
            # print(data) #debug
            # break if there is no device
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
                    intraday_dates = list(self.range_dates(datetime.strptime(self.startDate, '%Y-%m-%d').date(),
                                                      datetime.strptime(self.endDate, '%Y-%m-%d').date()))
                    for one_date in intraday_dates:
                        # Grab the result for the next date
                        result = self.data_retriever.api_map[data_key](str(one_date),
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
                self.directory = self.make_dir(self.user.device_type)  # set output path
                data = [self.flatten_dictionary(d) for d in data]
                df = pd.DataFrame(data)
                df['userid'] = self.user.user_id
                table = data_value

                try:
                    with connect_to_database(FITBIT_DATABASE) as fitbit_db:
                        # remove last days' device data
                        if table == "devices":
                            df['lastUpdate'] = self.endDate
                            modify_db.remove_device_data(self.user.user_id, fitbit_db, self.user.device_type)
                        df.to_sql(con=self.engine, name=table, if_exists='append')
                    # write to csv
                    filepath = os.path.join(self.directory, f"{table}.csv")
                    with open(filepath, 'a') as f:
                        df.to_csv(f, header=f.tell() == 0, encoding='utf-8', index=False)
                except Exception as e:
                    print(e)
                    continue
        return data_flag

    def range_dates(self, startDate, endDate, step=1):
        for i in range((endDate - startDate).days):
            yield startDate + timedelta(days=step * i)

    def flatten_dictionary(self, some_dict, parent_key='', separator='_'):
        flat_dict = {}
        for k, v in some_dict.items():
            new_key = parent_key + separator + k if parent_key else k
            new_key = new_key.replace(' ', '')
            if isinstance(v, list):
                continue  # v = dict([(x['name'], x) for x in v])
            if isinstance(v, dict):
                flat_dict.update(self.flatten_dictionary(v, parent_key=new_key))
            else:
                flat_dict[new_key] = v
        return flat_dict

    def make_dir(self, device):
        new_path = os.path.join(self.filepath, f"exported_data/{device}")
        output_path = os.path.join(new_path, self.startDate)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        return output_path
