'''Insert data into table'''
from sqlalchemy import create_engine
import pandas as pd
from modules.mysql.setup import connect_to_database

PATIENT_DATABASE = 'patient_labels'

def run_command(engine, command):
    with engine.connect() as con:
        rs = con.execute(command)

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


def update_patientid(engine, userid, new_patientid):
    command = f'''
    REPLACE INTO patient_label (userid, patientid)
    VALUES ('{userid}', '{new_patientid}');
    '''
    run_command(engine, command)

def get_patientid(engine, userid):
    command = f'''
    SELECT patientid
    FROM patient_ids
    WHERE userid = '{userid}';
    '''
    with engine.connect() as con:
        rs = con.execute(command)
    id_list = list(rs)
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

def export_patient_data(userid,patient_id, device_type, db):
    mycursor = db.cursor()
    command = f"INSERT INTO patient_ids VALUES (' {userid}', '{device_type}', '{patient_id}')"
    mycursor.execute(command)
    db.commit()

def test_insertion():
    data_to_insert = [['user_id', 'patientid', 'device_type',
                       'access_token', 'refresh_token', '12345'], ]
    engine = create_engine(
        f'mysql+pymysql://writer:password@localhost/device_info')
    insert_list_into('patient_ids', data_to_insert, engine)

if __name__ == "__main__":
    test_insertion()
    #DELETE FROM auth_info WHERE userid='BD6RKR'

