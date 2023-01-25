'''Insert data into table'''
from sqlalchemy import create_engine
import pandas as pd

def run_command(engine, command):
    with engine.connect() as con:
        con.execute(command)

def insert_list_into(table: str, items: list, engine):

    # Get the column names
    with engine.connect() as con:
        rs = con.execute(f'SHOW COLUMNS FROM {table};')
    colnames = [cinfo[0] for cinfo in list(rs)]

    # If there is id, then skip
    for i, colname in enumerate(colnames):
        if '_id' in colname:
            colnames = colnames[:i] + colnames[i+1:]
            break

    print("before query creation")

    # convert items (a nested list) to a dataframe 
    df = pd.DataFrame(items, columns=colnames)

    print(df, '\n\n\n')
    df.to_sql(con=engine, name=table, if_exists='append', index=False)

    print(f"{len(items)} new rows were inserted.")


def update_patientid(engine, userid, new_patient_id):
    command = f'''
    INSERT INTO patient_ids (userid, patient_id) VALUES ('{userid}', '{new_patient_id}') 
    ON DUPLICATE KEY UPDATE device_type=VALUES(device_type);
    '''
    run_command(engine, command)

def get_patientid(engine, userid):
    command = f'''
    SELECT patient_id
    FROM patient_ids
    WHERE userid = '{userid}';
    '''
    with engine.connect() as con:
        rs = con.execute(command)
    id_list = list(rs)
    print(id_list)
    return id_list[0][0] if id_list else ''

def add_web_app_user(email, hashed_password, username, db):
    db.cursor().execute(f"INSERT INTO login_info VALUES ('{email}', '{hashed_password}', '{username}')")
    db.commit()

def remove_web_app_user(email, db):
    db.cursor().execute(f"DELETE FROM login_info WHERE email='{email}'")
    db.commit()

def remove_fitbit_patient(patient_id, user_id, fitbit_db, auth_db):
    # TODO: check if patient exists in both databases before running
    # remove patient from fitbit database
    cursor = fitbit_db.cursor()
    cursor.execute(f"SELECT * FROM patient_ids WHERE patient_id='{patient_id}'")
    if cursor.fetchone():
        cursor.execute(f"DELETE FROM patient_ids WHERE patient_id='{patient_id}'")
        fitbit_db.commit()
    remove_heath_data(user_id, fitbit_db)

    # remove patient from auth database
    user_id = user_id.replace(' ', '') #spaces must be removed from strings
    cursor = auth_db.cursor()
    cursor.execute(f"SELECT * FROM auth_info WHERE userid='{user_id}'")
    if cursor.fetchone():
        cursor.execute(f"DELETE FROM auth_info WHERE userid='{user_id}'")
        auth_db.commit()

def link_user_to_key(key, email, db):
    db.cursor().execute(f"UPDATE registration_keys SET email = '{email}' WHERE user_key = '{key}'")
    db.commit()

def export_patient_data(userid, patient_id, device_type, db):
    mycursor = db.cursor()
    command = f"INSERT INTO patient_ids (userid, patient_id, device_type) VALUES ('{userid}', '{patient_id}', '{device_type}')"
    mycursor.execute(command)
    db.commit()

def update_auth_token(connection, userid, new_auth_token):
    command = f'''
    UPDATE Auth_info
    SET auth_token = '{new_auth_token}'
    WHERE userid = '{userid}';
    '''
    cursor = connection.cursor()
    cursor.execute(command)
    connection.commit()

def update_refresh_token(connection, userid, new_refresh_token):
    command = f'''
    UPDATE Auth_info
    SET refresh_token = '{new_refresh_token}'
    WHERE userid = '{userid}';
    '''
    cursor = connection.cursor()
    cursor.execute(command)
    connection.commit()

def test_insertion():
    data_to_insert = [['user_id', 'patientid', 'device_type',
                       'access_token', 'refresh_token', '12345'], ]
    engine = create_engine(
        f'mysql+pymysql://writer:password@localhost/device_info')
    insert_list_into('patient_ids', data_to_insert, engine)

#Remove health data from fitbit database
def remove_heath_data(user_id, fitbit_db):
    list = ['devices', 'activitiessteps', 'weight', "activitiesheart", "activitiesheartintraday", "activitiesstepsintraday"]

    cursor = fitbit_db.cursor()
    for data in list:
        try:
            cursor.execute(f"DELETE FROM {data} WHERE userid='{user_id}'")
        except:
            print(f"{data} table does not exist")
    fitbit_db.commit()

if __name__ == "__main__":
    test_insertion()
    #DELETE FROM auth_info WHERE userid='BD6RKR'

