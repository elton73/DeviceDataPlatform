'''Setup the DB to store authentication codes'''
from sqlalchemy import create_engine
import pymysql, os

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

TABLE_NAMES = ['patient_ids']

# TODO: CREATE this mysql user and GRANT them ALL PRIVILEGES if you haven't
USER = 'writer'
PASSWORD = 'password'
DATABASE_NAMES = ['fitbit', 'withings', 'polar'] # add databases for new devices
DATABASE_AUTH = 'authorization_info' #add database for authorization info

def run_commands(engine, command_list):
    with engine.connect() as con:
        for command in command_list:
            rs = con.execute(command, multi=True)
    return rs   # return result from last command in list

def make_engine(database=''):
    return create_engine(
        f'mysql+pymysql://{USER}:{PASSWORD}@localhost/{database}')

def create_dbs():
    engine = make_engine()

    for db in DATABASE_NAMES:
        commands = [f"CREATE DATABASE IF NOT EXISTS {db};",
                    f"USE {db};",
                    SQL_CREATE_DEVICE_TABLE];
        run_commands(engine, commands)

    # Create database for authorization codes
    commands = [f"CREATE DATABASE IF NOT EXISTS {DATABASE_AUTH};",
                f"USE {DATABASE_AUTH};",
                SQL_CREATE_AUTH_TABLE]

    run_commands(engine, commands)


if __name__ == "__main__":
    create_dbs()
