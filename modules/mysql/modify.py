'''Insert data into table'''
import requests
import pandas as pd
from modules import FITBIT_TABLES, WITHINGS_TABLES, POLAR_TABLES
from modules.mysql.setup import select_database

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


#todo: check if patient_id already exists before updating
def update_patientid(patient_id, new_patient_id, dbs):
    if not isinstance(dbs, list):
        dbs = [dbs]
    for db in dbs:
        cursor = db.cursor()
        cursor.execute(f'''
                        UPDATE patient_ids SET patient_id = '{new_patient_id}' where patient_id = '{patient_id}';
                        ''')
        db.commit()

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

def remove_patient(patient_id, user_id,device_type, device_db, auth_db):
    user_id = user_id.replace(' ', '')  # spaces must be removed from strings
    auth_cursor = auth_db.cursor()
    device_cursor = device_db.cursor(buffered=True)

    """
        Remove polar user registration
    """
    if device_type == "polar":
        # check if user has a member_id
        device_cursor.execute(f"SELECT member_id FROM member_ids WHERE userid='{user_id}'")
        member_id = device_cursor.fetchone()
        #reformat incoming data
        member_id = member_id[0] if member_id else member_id
        if member_id:
            result = auth_cursor.execute(f'SELECT auth_token FROM auth_info WHERE userid = "{user_id}"')
            token = auth_cursor.fetchone()
            #reformat incoming data
            token = token[0] if token else token
            # remove member_id from API
            requests.delete(f'https://www.polaraccesslink.com/v3/users/{user_id}', headers={
                'Authorization': f'Bearer {token}'})

    # remove patient from device's database
    device_cursor.execute(f"SELECT * FROM patient_ids WHERE patient_id='{patient_id}'")
    if device_cursor.fetchone():
        device_cursor.execute(f"DELETE FROM patient_ids WHERE patient_id='{patient_id}'")
        device_db.commit()

    #remove health related data
    remove_health_data(user_id, device_db, device_type)

    # remove patient from auth database
    auth_cursor.execute(f"SELECT * FROM auth_info WHERE userid='{user_id}'")
    if auth_cursor.fetchone():
        auth_cursor.execute(f"DELETE FROM auth_info WHERE userid='{user_id}'")
        auth_db.commit()


def link_user_to_key(key, email, db):
    db.cursor().execute(f"UPDATE registration_keys SET email = '{email}' WHERE user_key = '{key}'")
    db.commit()

def export_patient_data(userid, patient_id, device_type, db):
    mycursor = db.cursor()
    command = f"INSERT INTO patient_ids (userid, patient_id, device_type) VALUES ('{userid}', '{patient_id}', '{device_type}')"
    mycursor.execute(command)
    #Create member_id row for Polar devices
    if device_type == "polar":
        command = f"INSERT INTO member_ids (userid) VALUES ('{userid}')"
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

def remove_device_data(user_id, db, device_type):
    cursor = db.cursor()
    # remove data from fitbit database
    if device_type == "fitbit":
        try:
            cursor.execute(f"DELETE FROM devices WHERE userid='{user_id}'")
        except Exception as e:
            print(e)
        db.commit()
        return
    # remove data from withings database
    elif device_type == "withings":
        try:
            cursor.execute(f"DELETE FROM devices WHERE userid='{user_id}'")
        except Exception as e:
            print(e)
        db.commit()
        return

#Remove health data from fitbit database
def remove_health_data(user_id, db, device_type):
    cursor = db.cursor()
    #remove data from fitbit database
    if device_type == "fitbit":
        for key in FITBIT_TABLES:
            try:
                cursor.execute(f"DELETE FROM {FITBIT_TABLES[key]} WHERE userid='{user_id}'")
            except:
                print(f"{FITBIT_TABLES[key]} table does not exist")
        db.commit()
        return

    # remove data from withings database
    elif device_type == "withings":
        #special case for devices table
        try:
            cursor.execute(f"DELETE FROM devices WHERE userid='{user_id}'")
        except Exception as e:
            print(e)
        for key in WITHINGS_TABLES:
            try:
                cursor.execute(f"DELETE FROM {WITHINGS_TABLES[key]} WHERE userid='{user_id}'")
            except:
                print(f"{WITHINGS_TABLES[key]} table does not exist")
        db.commit()
        return

    # remove data from polar database
    elif device_type == "polar":
        # remove member_id
        cursor.execute(f"DELETE FROM member_ids WHERE userid='{user_id}'")

        for key in POLAR_TABLES:
            try:
                cursor.execute(f"DELETE FROM {POLAR_TABLES[key]} WHERE userid='{user_id}'")
            except:
                print(f"{POLAR_TABLES[key]} table does not exist")
        db.commit()
        return
    return False

# Input (userid, device_type, auth_token, refresh_token, and expires by) data into mysql
def export_device_to_auth_info(auth_info, db):
    userid = auth_info['user_id']
    device_type = auth_info['device_type']
    auth_token = auth_info['access_token']
    refresh_token = auth_info['refresh_token']
    expires_by = auth_info['expires_in']  #todo: change to expires by later

    mycursor = db.cursor()
    command = f"INSERT INTO auth_info (userid, device_type, auth_token, refresh_token, expires_by) VALUES ('{userid}' , '{device_type}', '{auth_token}', '{refresh_token}', '{expires_by}')"
    mycursor.execute(command)
    db.commit()

if __name__ == "__main__":
    for key in FITBIT_TABLES:
        print(FITBIT_TABLES[key])





