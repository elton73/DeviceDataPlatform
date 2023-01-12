'''Setup the DB to store authentication codes'''
from sqlalchemy import create_engine
import pymysql, os

SQL_CREATE_DEVICE_TABLE = '''
CREATE TABLE IF NOT EXISTS patient_ids(
    userid VARCHAR(30) NOT NULL PRIMARY KEY,
    patientid VARCHAR(30) NOT NULL);
'''

TABLE_NAMES = ['patient_ids']

# TODO: CREATE this mysql user and GRANT them ALL PRIVILEGES if you haven't
USER = 'writer'
PASSWORD = 'password'
DATABASE_NAMES = ['fitbit', 'withings', 'polar'] # add databases for new devices

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


if __name__ == "__main__":
    create_dbs()
