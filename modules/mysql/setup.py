'''Setup the DB to store authentication codes'''
from sqlalchemy import create_engine, text
from mysql import connector
from modules import FITBIT_DATABASE, WITHINGS_DATABASE, POLAR_DATABASE, AUTH_DATABASE, LOGIN_DATABASE, USER, PASSWORD, \
    EMAILS_DATABASE

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
    email VARCHAR(254) NOT NULL PRIMARY KEY);
'''

SQL_CREATE_KEY_TABLE = '''
CREATE TABLE IF NOT EXISTS registration_keys(
    user_key VARCHAR(10) NOT NULL PRIMARY KEY,
    email VARCHAR(254));
'''

SQL_CREATE_PATIENT_DEVICE_TABLE = '''
CREATE TABLE IF NOT EXISTS patient_ids(
    patient_id VARCHAR(30),
    userid VARCHAR(30) NOT NULL PRIMARY KEY,
    device_type VARCHAR(30) NOT NULL);
'''

SQL_CREATE_POLAR_MEMBER_ID_TABLE = '''
CREATE TABLE IF NOT EXISTS member_ids(
    userid VARCHAR(30) NOT NULL PRIMARY KEY,
    member_id VARCHAR(254));
'''

# TODO: CREATE this mysql user and GRANT them ALL PRIVILEGES if you haven't
DEVICE_DATABASES = [FITBIT_DATABASE, WITHINGS_DATABASE, POLAR_DATABASE] # add databases for new devices

def run_commands(engine, command_list):
    with engine.connect() as con:
        for command in command_list:
            rs = con.execute(text(command))
    return rs   # return result from last command in list

def make_engine(database=''):
    return create_engine(
        f'mysql+pymysql://{USER}:{PASSWORD}@localhost/{database}')

def create_dbs(engine, database_names, create_table):
    if not isinstance(database_names, list):
        database_names = [database_names]
    for db in database_names:
        commands = [f"CREATE DATABASE IF NOT EXISTS {db};",
                    f"USE {db};",
                    create_table];
        run_commands(engine, commands)

def create_table(engine, database_names, create_table):
    if not isinstance(database_names, list):
        database_names = [database_names]
    for db in database_names:
        commands = [f"CREATE DATABASE IF NOT EXISTS {db};",
                    f"USE {db};",
                    create_table];
        run_commands(engine, commands)

# establish database connection
def connect_to_database(databasename):
    database = connector.connect(
        host='localhost',
        user=USER,
        passwd=PASSWORD,
        database=databasename,
    )
    return database

def select_database(device_type):
    if device_type == "fitbit":
        return FITBIT_DATABASE
    elif device_type == "withings":
        return WITHINGS_DATABASE
    elif device_type == "polar":
        return POLAR_DATABASE
    elif device_type == "all":
        return [FITBIT_DATABASE,
                WITHINGS_DATABASE,
                POLAR_DATABASE]

#setup all databases
def setup_databases():
    engine = make_engine()
    create_dbs(engine, AUTH_DATABASE, SQL_CREATE_AUTH_TABLE)
    create_dbs(engine, EMAILS_DATABASE, SQL_CREATE_EMAIL_LIST_TABLE)
    create_dbs(engine, DEVICE_DATABASES, SQL_CREATE_PATIENT_DEVICE_TABLE)
    create_dbs(engine, LOGIN_DATABASE, SQL_CREATE_WEBAPP_LOGIN_INFO_TABLE)
    create_table(engine, LOGIN_DATABASE, SQL_CREATE_KEY_TABLE)
    create_key("0123456789")
    create_table(engine, POLAR_DATABASE, SQL_CREATE_POLAR_MEMBER_ID_TABLE)

#Generate sign up key
def create_key(key):
    if key.isalnum():
        command = f"""
        INSERT IGNORE INTO registration_keys (user_key) VALUES ('{key}')
        """
        with connect_to_database(LOGIN_DATABASE) as db:
            mycursor = db.cursor()
            mycursor.execute(command)
            db.commit()
    else:
        print("Invalid Key")

# if __name__ == "__main__":
#     create_key("123456789")





