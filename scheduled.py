'''Launch the Main Application here
'''
import modules.fitbit.authentication as auth
import modules.fitbit.retrieve as fitbit_retrieve
import modules.mysql.setup as setup_db
import modules.mysql.modify as modify_db
import modules.mysql.report as report_db
from pathlib import Path
import sys, os
import pandas as pd
from datetime import datetime, timedelta, timezone, date

from modules.web_app import AUTH_DATABASE, ENGINE
try:
    import httplib  # python < 3.0
except:
    import http.client as httplib
import time

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

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

def range_dates(startDate, endDate, step=1):
    for i in range((endDate-startDate).days):
        yield startDate + timedelta(days=step*i)

def drop_table(engine, table):
    conn = engine.raw_connection()
    cursor = conn.cursor()
    command = "DROP TABLE IF EXISTS {};".format(table)
    cursor.execute(command)
    conn.commit()
    cursor.close()

def writeSQLData(auth_conn, selected_user_ids, selectedDataTypes):
    '''Grab the users, the data types, the date range'''

    # Selected user IDs must be wrapped with single quotes for SQLite Query
    query_selected_user_ids = list(map(lambda text: f'\'{text}\'', selected_user_ids))
    access_tokens = report_db.get_auth_tokens(auth_conn, query_selected_user_ids)
    refresh_tokens = report_db.get_refresh_tokens(auth_conn, query_selected_user_ids)

    startDate = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')         # yesterday
    endDate = date.today().strftime('%Y-%m-%d')                               # today

    drop_table(ENGINE, 'devices')

    request_num = 0
    start_time = time.time()
    for userid in selected_user_ids:

        errorFlag = False
        UserDataRetriever = fitbit_retrieve.DataGetter(access_tokens[userid])
        for dataType in selectedDataTypes:
            print(dataType, startDate, endDate)
            result = UserDataRetriever.fitbit_api_map[dataType](startDate, endDate)
            if result.status_code == 401:
                # Expired token
                new_auth_info = auth.get_refreshed_auth_info(userid, refresh_tokens[userid])

                # Bad Refresh Token
                if new_auth_info == 400:
                    print("Bad refresh token")
                    continue

                # If There is a problem with getting new auth info, skip
                if new_auth_info == '':
                    break

                # Update the database
                modify_db.update_auth_token(auth_conn, userid, new_auth_info['access_token'])
                modify_db.update_refresh_token(auth_conn, userid, new_auth_info['refresh_token'])
                # Update the retriever
                UserDataRetriever.token = new_auth_info['access_token']
                # Try the request again

                print(startDate, endDate)
                result = UserDataRetriever.fitbit_api_map[dataType](startDate, endDate)

            print('dataType', dataType)
            # Get the data. If intraday, it is the first date
            data = result.json()

            print(data)
            request_num += 1
            # Most likely too many request error here:

            if type(data) is dict:
                if 'errors' in list(data.keys()):
                    errorFlag = True
                    break

                # Get the first list
                for key in dataType.split(' '):
                    data = data[key]

                # Handle Intraday - selection includes 'dataset'... since intraday can only grab one day
                if len(dataType.split(' ')) > 1 and dataType.split(' ')[1] == 'dataset':
                    data =[]
                    intraday_dates = list(range_dates(datetime.strptime(startDate, '%Y-%m-%d').date(), datetime.strptime(endDate, '%Y-%m-%d').date()))
                    for one_date in intraday_dates:
                        # Grab the result for the next date
                        result = UserDataRetriever.fitbit_api_map[dataType](str(one_date), endDate) # Since one_date is a datetime.date
                        next_day_data = result.json()

                        # Fitbit only returns the time so format it into a datetime

                        for key in dataType.split(' '):
                            next_day_data = next_day_data[key]
                        # Format time to datetime
                        next_day_data = [{'datetime': datetime.strptime(f"{str(one_date)} {data['time']}", "%Y-%m-%d %H:%M:%S"), 'value': data['value']} for data in next_day_data]
                        # There should only be a list left
                        data += next_day_data
                        request_num += 1


            # Data is sometimes weirdly formatted with nested dictionaries. Flatten the data
            # data = [flatten_dictionary(d) for d in data]
            # Format the data as a dataframe

            if len(data):
                print(data[0])

                data = [flatten_dictionary(d) for d in data]
                print('data: ', data)
                df = pd.DataFrame(data)
                df['userid'] = userid

                print(df.head())
                print(df.info())

                table = dataType.replace('-','').replace(' dataset', '')
                try:
                    df.to_sql(con=ENGINE, name=table, if_exists='append')
                except:
                    continue


    print(f'Time Elapsed for {request_num} requests = {time.time()-start_time}')


if __name__ == '__main__':

    auth_db = setup_db.connect_to_database(AUTH_DATABASE)
    user_ids = report_db.get_all_user_ids(auth_db)
    selected_datatypes = ['devices', 'activities-steps', 'sleep', 'activities-heart-intraday dataset', 'activities-steps-intraday dataset']

    writeSQLData(auth_db, user_ids, selected_datatypes)
