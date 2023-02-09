from sqlalchemy import create_engine

USER = 'newwriter'
PASSWORD = 'password'
FITBIT_DATABASE = 'fitbit_test'
WITHINGS_DATABASE = 'withings_test'
POLAR_DATABASE = 'polar_test'
AUTH_DATABASE = 'authorization_info_test'
LOGIN_DATABASE = 'webapp_login_info'
# EMAILS_DATABASE = ['email_list'] #add database for list of emails
FITBIT_ENGINE = create_engine('mysql+pymysql://newwriter:password@localhost/fitbit_test')
WITHINGS_ENGINE = create_engine('mysql+pymysql://newwriter:password@localhost/withings_test')
POLAR_ENGINE = create_engine('mysql+pymysql://newwriter:password@localhost/polar_test')

# fitbit data
FITBIT_TABLES = {'devices': 'devices',
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