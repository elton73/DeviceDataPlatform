"""
Update class for updating a user information
"""
import modules.fitbit.retrieve as fitbit_retrieve
from modules.mysql.setup import connect_to_database
import modules.mysql.modify as modify_db
import modules.mysql.report as report_db
import pandas as pd
from datetime import datetime, timedelta, date
from modules import AUTH_DATABASE, FITBIT_TABLES, FITBIT_DATABASE
import os
import math


class Fitbit_Update():
    def __init__(self, user, startDate, endDate, filepath, engine):
        self.user = user
        self.datetime_format = "%Y-%m-%d"
        self.startDate = datetime.strptime(startDate, self.datetime_format).date()
        self.endDate = datetime.strptime(endDate, self.datetime_format).date()
        self.data_retriever = fitbit_retrieve.DataGetter(user.access_token)
        self.engine = engine
        self.filepath = filepath

        self.days_to_update = 1
        self.last_sync_date = None
        self.update_flag = False  # Flag for checking last sync date
        self.is_manual_update = False

        self.send_email = False

    def update(self):
        data_flag = False  # Flag for if user has data to be uploaded to mysql
        while self.days_to_update > 0:
            for data_key, data_value in FITBIT_TABLES.items():
                result = self.data_retriever.api_map[data_key](self.startDate.strftime(self.datetime_format),
                                                               self.endDate.strftime(self.datetime_format))

                # If token expired, get a new token and retrieve data again
                if result.status_code == 401:
                    # debug
                    print(f"Result Code: 401 for user: {self.user.user_id}")
                    new_auth_info = self.user.get_refreshed_fitbit_auth_info()
                    # If There is a problem with getting new auth info, skip
                    if new_auth_info == '':
                        break
                    # Update the database
                    with connect_to_database(AUTH_DATABASE) as auth_db:
                        self.user.access_token = modify_db.update_auth_token(auth_db, self.user.user_id,
                                                                             new_auth_info['access_token'])
                        self.user.refresh_token = modify_db.update_refresh_token(auth_db, self.user.user_id,
                                                                                 new_auth_info['refresh_token'])
                    # Update the retriever
                    self.data_retriever.token = new_auth_info['access_token']
                    result = self.data_retriever.api_map[data_key](self.startDate.strftime(self.datetime_format),
                                                                   self.endDate.strftime(self.datetime_format))
                data = result.json()

                # if there is no device connected to the fitbit account, break
                if data_key == "devices":
                    if data == []:
                        break
                    # Make sure to only update the device if the device has been synced and new data is available.
                    # Otherwise, the database will be updated with "zero" data. (Ex. 0 Steps taken).
                    if not self.update_flag and not self.is_manual_update:
                        #  get the date the device was last updated to the database
                        with connect_to_database(FITBIT_DATABASE) as fitbit_db:
                            last_update = report_db.get_last_update(self.user.user_id, fitbit_db)
                        if last_update:
                            last_update = datetime.strptime(last_update, "%Y-%m-%d")
                            for device in data:
                                self.last_sync_date = datetime.strptime(device['lastSyncTime'], "%Y-%m-%dT%H:%M:%S.%f")
                            # Find how many days were missed due to fitbit sync
                            self.days_to_update = (self.last_sync_date - last_update).days
                            if self.days_to_update > 0:
                                self.startDate = last_update.date()
                                self.endDate = (last_update + timedelta(days=1)).date()
                                self.update_flag = True
                                if self.days_to_update > 3:
                                    self.send_email = True
                            else:
                                return data_flag

                if type(data) is dict:
                    if 'errors' in list(data.keys()):
                        break

                    # Get the first list
                    for key in data_key.split(' '):
                        data = data[key]

                    # Handle Intraday - selection includes 'dataset'... since intraday can only grab one day
                    if len(data_key.split(' ')) > 1 and data_key.split(' ')[1] == 'dataset':
                        data = []
                        intraday_dates = list(self.range_dates(self.startDate,
                                                               self.endDate))
                        for one_date in intraday_dates:
                            # Grab the result for the next date
                            result = self.data_retriever.api_map[data_key](str(one_date),
                                                                           self.endDate.strftime(self.datetime_format))
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
                    df['patient_id'] = self.user.patient_id
                    table = data_value

                    with connect_to_database(FITBIT_DATABASE) as fitbit_db:
                        # remove last days' device data
                        if table == "devices":
                            # Check if self.endDate is closer to the future than the last time the device was updated
                            last_update = report_db.get_last_update(self.user.user_id, fitbit_db)
                            if not last_update:
                                df['lastUpdate'] = self.endDate
                            elif self.endDate > datetime.strptime(last_update, "%Y-%m-%d").date():
                                df['lastUpdate'] = self.endDate
                            else:
                                df['lastUpdate'] = datetime.strptime(last_update, "%Y-%m-%d").date()
                            modify_db.remove_device_data(self.user.user_id, fitbit_db, self.user.device_type)

                        # try to upload df into mysql. If this fails, try to repair the sql table and upload again
                        try:
                            df.to_sql(con=self.engine, name=table, if_exists='append')
                        except:
                            try:
                                modify_db.repair_sql_table(df, fitbit_db, FITBIT_DATABASE, table)
                                df.to_sql(con=self.engine, name=table, if_exists='append')
                            except Exception as e:
                                print(f"df.to_sql failed for user: {self.user.user_id}")
                                print(e)

                    # write to csv
                    filepath = os.path.join(self.directory, f"{table}.csv")
                    with open(filepath, 'a') as f:
                        df.to_csv(f, header=f.tell() == 0, encoding='utf-8', index=False)
            self.startDate += timedelta(days=1)
            self.endDate += timedelta(days=1)
            self.days_to_update -= 1
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
        new_path = os.path.join(self.filepath, f"exported_data/{self.user.patient_id}")
        output_path = os.path.join(new_path, device)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        return output_path
