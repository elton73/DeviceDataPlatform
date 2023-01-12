'''Setup the DB to store authentication codes'''
import os
import sqlite3

DATABASE_NAME = 'db.sqlite3'

SQL_ENABLE_FOREIGN_KEY = '''
PRAGMA foreign_keys = ON; 
'''
SQL_CREATE_AUTH_TABLE = '''
CREATE TABLE IF NOT EXISTS Auth_info(
    userid TEXT NOT NULL PRIMARY KEY,
    device_type TEXT NOT NULL,
    auth_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_by INTEGER NOT NULL);
'''

TABLE_NAMES = ['Auth_info']

def drop_all_tables(table_names):
    return [f'DROP TABLE IF EXISTS {table};' for table in table_names]

def insert_list_into(table: str, items: list, connection, label_exists=False):
    cursor = connection.cursor()
    cursor.execute(f'SELECT * FROM {table}')
    # Get the column names
    colnames = [description[0] for description in cursor.description]
    
    # If there is id, then skip
    for i, colname in enumerate(colnames):
        if '_id' in colname:
            colnames = colnames[:i] + colnames[i+1:]
            break

    # If label does not exist we will use the default values, so exclude it from data entry
    if not label_exists:
        for i, colname in enumerate(colnames):
            if 'label' in colname:
                colnames = colnames[:i] + colnames[i+1:]
                break
    

    # Make the insert command
    insert_command = f'INSERT INTO {table}('
    values_portion = 'VALUES ('
    for i, colname in enumerate(colnames):
        insert_command += colname
        values_portion += '?'
        # Not Last entry
        if i != len(colnames)-1:
            insert_command += ', '
            values_portion += ', '
    values_portion += ')'
    insert_command += ') ' + values_portion
    connection.executemany(insert_command, items)
    connection.commit()

def run_commands(connection, command_list):
    cursor = connection.cursor()
    for command in command_list:
        cursor.execute(command)
        connection.commit()

def create_db(dir_path=os.getcwd()):

    if os.path.exists(os.path.join(dir_path, DATABASE_NAME)):
        return
    
    conn = sqlite3.connect(os.path.join(dir_path, DATABASE_NAME))

    commands = [SQL_ENABLE_FOREIGN_KEY,
                SQL_CREATE_AUTH_TABLE]
    
    run_commands(conn, commands)

if __name__=="__main__":
    create_db()
    