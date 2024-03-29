import os

#Database user
USER = os.environ.get("SECRET_USER")
PASSWORD = os.environ.get("SECRET_PASSWORD")

#Databases
FITBIT_DATABASE = 'fitbit_2'
WITHINGS_DATABASE = 'withings_2'
POLAR_DATABASE = 'polar_2'
AUTH_DATABASE = 'authorization_info_2'
LOGIN_DATABASE = 'webapp_login_info_2'
EMAILS_DATABASE = 'email_list'

# fitbit data
FITBIT_TABLES = {'devices': 'devices', # Note: it is important that the first element of this table is devices because
                 # the updater needs to get the last_sync_time from this row before updating anything else
                 'activities-steps': 'activitiessteps',
                 'sleep': 'sleep',
                 'activities-heart-intraday dataset': 'activitiesheartintraday',
                 'activities-steps-intraday dataset': 'activitiesstepsintraday'
                 }
# withings data
# {withings_key: mysql_table_name}
WITHINGS_TABLES = {'hr': 'heart_rate', 'rr': 'respiration_rate',
                   'snoring': 'snoring_time', "data": "sleep_time"}
# {withings_column_name: mysql_column_name}
WITHINGS_COLUMNS = {'total_sleep_time': "minutesAsleep",
                    "waso": "minutesAwake"}

# polar data
POLAR_TABLES = {'exercise_summary': "exercise_summary",
                'heart_rate': "heart_rate"}