'''Setup the DB to store authentication codes'''
from sqlalchemy import create_engine
from mysql import connector

SQL_CREATE_DEVICE_TABLE = '''
CREATE TABLE IF NOT EXISTS patient_ids(
    userid VARCHAR(30) NOT NULL PRIMARY KEY,
    patientid VARCHAR(30) NOT NULL);
'''

SQL_CREATE_AUTH_TABLE = '''
CREATE TABLE IF NOT EXISTS Auth_info(
    userid VARCHAR(30) NOT NULL PRIMARY KEY,
    device_type VARCHAR(30) NOT NULL,
    auth_token VARCHAR(500) NOT NULL,
    refresh_token VARCHAR(500) NOT NULL,
    expires_by VARCHAR(50) NOT NULL);
'''

SQL_CREATE_WEBAPP_LOGIN_INFO_TABLE = '''
CREATE TABLE IF NOT EXISTS login_info(
    email VARCHAR(254) NOT NULL PRIMARY KEY,
    password VARCHAR(127) NOT NULL,
    username VARCHAR(20) NOT NULL);
'''

SQL_CREATE_EMAIL_LIST_TABLE = '''
CREATE TABLE IF NOT EXISTS email_list(
    email VARCHAR(254) NOT NULL PRIMARY KEY,
    patientid VARCHAR(30) NOT NULL);
'''

SQL_CREATE_KEY_TABLE = '''
CREATE TABLE IF NOT EXISTS registration_keys(
    user_key VARCHAR(10) NOT NULL PRIMARY KEY,
    email VARCHAR(254));
'''

SQL_CREATE_PATIENT_DEVICE_TABLE = '''
CREATE TABLE IF NOT EXISTS patient_label(
    patient_id VARCHAR(30),
    userid VARCHAR(30) NOT NULL PRIMARY KEY,
    device_type VARCHAR(30) NOT NULL);
'''

TABLE_NAMES = ['patient_ids']

# TODO: CREATE this mysql user and GRANT them ALL PRIVILEGES if you haven't
USER = 'writer'
PASSWORD = 'password'
DATABASE_NAMES = ['fitbit', 'withings', 'polar'] # add databases for new devices
DATABASE_AUTH = ['authorization_info'] #add database for authorization info
DATABASE_LOGIN = ['Webapp_login_info'] #add database for login info
DATABASE_EMAILS = ['email_list'] #add database for list of emails
DATABASE_PATIENT_LABEL = ['patient_labels']

def run_commands(engine, command_list):
    with engine.connect() as con:
        for command in command_list:
            rs = con.execute(command, multi=True)
    return rs   # return result from last command in list

def make_engine(database=''):
    return create_engine(
        f'mysql+pymysql://{USER}:{PASSWORD}@localhost/{database}')

def create_dbs(engine, database_names, create_table):
    for db in database_names:
        commands = [f"CREATE DATABASE IF NOT EXISTS {db};",
                    f"USE {db};",
                    create_table];
        run_commands(engine, commands)

def create_table(engine, database_names, create_table):
    for db in database_names:
        commands = [f"CREATE DATABASE IF NOT EXISTS {db};",
                    f"USE {db};",
                    create_table];
        run_commands(engine, commands)

# establish database connection
def connect_to_database(databasename):
    database = connector.connect(
        host='localhost',
        user='root',
        passwd='password',
        database=databasename
    )
    return database

def connect_to_server():
    # Connect to host server
    server = connector.connect(
        host='localhost',
        user='root',
        passwd='password',
    )
    return server


if __name__ == "__main__":
    engine = make_engine()

    # create_dbs(engine, DATABASE_PATIENT_LABEL, SQL_CREATE_PATIENT_DEVICE_TABLE)
    # create_table(engine, DATABASE_LOGIN, SQL_CREATE_KEY_TABLE)


