"""
Update class for updating a user information
"""
import modules.withings.retrieve as withings_retrieve
from modules.mysql.setup import connect_to_database
import modules.mysql.modify as modify_db
import pandas as pd
from datetime import datetime
from modules import AUTH_DATABASE, WITHINGS_TABLES, WITHINGS_COLUMNS, WITHINGS_DATABASE
import os

class Withings_Update():
    def __init__(self, user, startDate, endDate, filepath, engine):
        self.user = user
        self.startDate = startDate
        self.endDate = endDate
        self.data_retriever = withings_retrieve.DataGetter(user.access_token)
        self.engine = engine
        self.filepath = filepath

    def update(self):
        device_data = []
        data_flag = False  # Flag for if user has data to be uploaded to mysql
        for data_key, data_value in WITHINGS_TABLES.items():
            result = self.data_retriever.api_map[data_value](self.startDate, self.endDate)
            raw_data = result.json()
            # error codes
            if str(raw_data['status']) == '401':
                new_auth_info = self.user.get_refreshed_withings_auth_info()['body']
                if str(new_auth_info) == '400':
                    break
                if new_auth_info == '':
                    break
                # Update the database
                with connect_to_database(AUTH_DATABASE) as auth_db:
                    modify_db.update_auth_token(auth_db, self.user.user_id, new_auth_info['access_token'])
                    modify_db.update_refresh_token(auth_db, self.user.user_id, new_auth_info['refresh_token'])
                # Update the retriever
                self.data_retriever.token = new_auth_info['access_token']
                raw_data = self.data_retriever.api_map[data_value](self.startDate, self.endDate).json()
            data = raw_data['body']['series']
            # print(data) #debug
            # if there is no data, move on
            if not data:
                break
            else:
                self.directory = self.make_dir(self.user.device_type)  # set output path
                data_flag += 1
                # reformat data before creating dataframe
                formatted_data = self.format_withings_data(data, data_key)
                df = pd.DataFrame(formatted_data)
                df['userid'] = self.user.user_id
                table = data_value.replace('-', '').replace(' dataset', '')
                try:
                    df.to_sql(con=self.engine, name=table, if_exists='append')
                    # Export data
                    filepath = os.path.join(self.directory, f"{table}.csv")
                    with open(filepath, 'a') as f:
                        df.to_csv(f, header=f.tell() == 0, encoding='utf-8', index=False)
                except Exception as e:
                    print(e)
            # Manually update device data to mysql
            if not device_data:
                device_data = [{
                    'model': data[0][f'model'],
                }]
                device_df = pd.DataFrame(device_data)
                device_df['userid'] = self.user.user_id
                device_df['lastUpdate'] = self.endDate

                # Export data
                filepath = os.path.join(self.directory, f"{table}.csv")
                with open(filepath, 'a') as f:
                    df.to_csv(f, header=f.tell() == 0, encoding='utf-8', index=False)
                # remove last days device data
                with connect_to_database(WITHINGS_DATABASE) as withings_db:
                    modify_db.remove_device_data(self.user.user_id, withings_db, self.user.device_type)
                    device_df.to_sql(con=self.engine, name="devices", if_exists='append')
        return data_flag

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

    def pop_data(self, keys, dict):
        for key in keys:
            if key in dict:
                dict.pop(key)
        return dict

    def make_dir(self, device):
        new_path = os.path.join(self.filepath, f"exported_data/{device}")
        output_path = os.path.join(new_path, self.startDate)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        return output_path
