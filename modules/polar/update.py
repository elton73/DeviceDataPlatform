"""
Update class for updating polar user information
"""
import modules.polar.retrieve as polar_retrieve
from modules.mysql.setup import connect_to_database
import modules.mysql.modify as modify_db
import pandas as pd
from datetime import datetime, timedelta
from modules import POLAR_DATABASE, POLAR_TABLES
import os


class Polar_Update():
    def __init__(self, user, startDate, endDate, filepath, engine):
        self.user = user
        self.startDate = startDate
        self.endDate = endDate
        self.user_data_retriever = polar_retrieve.DataGetter(user.access_token, user.user_id)
        self.engine = engine
        self.filepath = filepath

    def update(self):
        member_id = self.user.check_polar_member_id()
        data_flag = False  # Flag for if user has data to be uploaded to mysql
        for data_key, data_value in POLAR_TABLES.items():
            data = self.user_data_retriever.api_map[data_value]()
            if not data:
                break
            else:
                data_flag = True
                self.directory = self.make_dir(self.user.device_type)  # set output path
            # format data
            if data_key == 'exercise_summary':
                formatted_data = self.format_exercise_summary(data, self.user)
            if data_key == 'heart_rate':
                formatted_data = self.format_heart_rate(data, self.user)

            # create panda dataframe
            df = pd.DataFrame(formatted_data)
            table = data_value.replace('-', '').replace(' dataset', '')

            # store data in database and csv
            # try to upload df into mysql. If this fails, try to repair the sql table and upload again
            try:
                df.to_sql(con=self.engine, name=table, if_exists='append')
            except:
                with connect_to_database(POLAR_DATABASE) as polar_db:
                    try:
                        modify_db.repair_sql_table(df, polar_db, POLAR_DATABASE, table)
                        df.to_sql(con=self.engine, name=table, if_exists='append')
                    except Exception as e:
                        print(f"df.to_sql failed for user: {self.user.user_id}")
                        print(e)

            #write to csv
            filepath = os.path.join(self.directory, f"{table}.csv")
            with open(filepath, 'a') as f:
                df.to_csv(f, header=f.tell() == 0, encoding='utf-8', index=False)

            # commit transaction. Old data will be deleted
            self.user_data_retriever.commit_transaction()
        return data_flag

    # Format polar exerise summary data
    def format_exercise_summary(self, data, user):
        for exercise_summary in data:
            # remove data columns
            pop_columns = ['upload-time', 'polar-user', 'has-route', 'detailed-sport-info', 'distance']
            for column in pop_columns:
                exercise_summary.pop(column, None)
            heart_rate = exercise_summary.pop('heart-rate')
            exercise_summary['start_time'] = exercise_summary.pop('start-time')

            # Catch if data is missing. Polar excludes these if they don't exist so we set it ourselves
            if not heart_rate:
                heart_rate['average'] = 0
                heart_rate['maximum'] = 0

            exercise_summary['hr_average'] = heart_rate['average']
            exercise_summary['hr_max'] = heart_rate['maximum']

            exercise_summary['userid'] = user.user_id
            exercise_summary['patient_id'] = user.patient_id
        return data

    # format polar heart_rate data
    def format_heart_rate(self, data, user):
        output = []
        index = 0
        for heart_rates in data:
            id = heart_rates['id']

            # format our own time since polar doesn't provide it
            with connect_to_database(POLAR_DATABASE) as db:
                cursor = db.cursor()
                cursor.execute(f"SELECT start_time FROM exercise_summary WHERE id='{id}'")
                raw_time = cursor.fetchone()
                formatted_time = raw_time[0].replace("T", " ") if raw_time else raw_time
                current_time = datetime.strptime(formatted_time, "%Y-%m-%d %H:%M:%S")

                recording_rate = heart_rates['recording-rate']
                for heart_rate in heart_rates['data'].split(","):
                    output.append({})
                    output[index]['id'] = id
                    output[index]['time'] = current_time
                    output[index]['value'] = int(float(heart_rate))
                    output[index]['userid'] = user.user_id
                    output[index]['patient_id'] = user.patient_id
                    index += 1
                    current_time = current_time + timedelta(seconds=recording_rate)
        return output

    def make_dir(self, device):
        new_path = os.path.join(self.filepath, f"exported_data/{self.user.patient_id}")
        output_path = os.path.join(new_path, device)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        return output_path