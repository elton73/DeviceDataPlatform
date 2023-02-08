'''Setup the DB to store authentication codes'''
from sqlalchemy import create_engine
from mysql import connector
from modules import FITBIT_DATABASE, WITHINGS_DATABASE, POLAR_DATABASE, AUTH_DATABASE, LOGIN_DATABASE, USER, PASSWORD

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
CREATE TABLE IF NOT EXISTS patient_ids(
    patient_id VARCHAR(30),
    userid VARCHAR(30) NOT NULL PRIMARY KEY,
    device_type VARCHAR(30) NOT NULL);
'''

# TODO: CREATE this mysql user and GRANT them ALL PRIVILEGES if you haven't
DEVICE_DATABASES = [FITBIT_DATABASE, WITHINGS_DATABASE, POLAR_DATABASE] # add databases for new devices

def run_commands(engine, command_list):
    with engine.connect() as con:
        for command in command_list:
            rs = con.execute(command, multi=True)
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
        database=databasename
    )
    return database

def setup_databases():
    engine = make_engine()
    create_dbs(engine, AUTH_DATABASE, SQL_CREATE_AUTH_TABLE)
    # create_dbs(engine, EMAILS_DATABASE, SQL_CREATE_EMAIL_LIST_TABLE)
    create_dbs(engine, DEVICE_DATABASES, SQL_CREATE_PATIENT_DEVICE_TABLE)
    create_dbs(engine, LOGIN_DATABASE, SQL_CREATE_WEBAPP_LOGIN_INFO_TABLE)
    create_table(engine, LOGIN_DATABASE, SQL_CREATE_KEY_TABLE)
    create_key("12345")
    #debug
    # print('success')

def create_key(key):
    if key.isnumeric():
        command = f"""
        INSERT IGNORE INTO registration_keys (user_key) VALUES ('{key}')
        """
        db = connect_to_database(LOGIN_DATABASE)
        mycursor = db.cursor()
        mycursor.execute(command)
        db.commit()
    else:
        print("Invalid Key")

if __name__ == "__main__":
    setup_databases()





