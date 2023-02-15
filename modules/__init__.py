from sqlalchemy import create_engine
from secret_keys import secrets

#Database user
USER = secrets.get('SECRET_USER')
PASSWORD = secrets.get('SECRET_PASSWORD')

#Databases
FITBIT_DATABASE = 'fitbit_test'
WITHINGS_DATABASE = 'withings_test'
POLAR_DATABASE = 'polar_test'
AUTH_DATABASE = 'authorization_info_test'
LOGIN_DATABASE = 'webapp_login_info'
DATABASE_USERS = 'USERS' #database readers and wriers
# EMAILS_DATABASE = ['email_list'] #add database for list of emails

FITBIT_ENGINE = create_engine(f'mysql+pymysql://{USER}:{PASSWORD}@localhost/{FITBIT_DATABASE}')
WITHINGS_ENGINE = create_engine(f'mysql+pymysql://{USER}:{PASSWORD}@localhost/{WITHINGS_DATABASE}')
POLAR_ENGINE = create_engine(f'mysql+pymysql://{USER}:{PASSWORD}@localhost/{POLAR_DATABASE}')

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

# polar data
POLAR_TABLES = {'exercise_summary': "exercise_summary",
                'heart_rate': "heart_rate"}