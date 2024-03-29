"""
Functions to fetch data from the SQL table
"""
from bcrypt import checkpw

def get_all_token_timeouts(connection):
    command = '''
    SELECT userid, expires_by FROM Auth_info;
    '''
    cursor = connection.cursor()
    cursor.execute(command)
    result = cursor.fetchall()
    return {data[0]: data[1] for data in result}

#get userids from auth database
def get_all_user_ids(connection):
    command = '''
    SELECT userid FROM Auth_info;
    '''
    cursor = connection.cursor()
    cursor.execute(command)
    result = cursor.fetchall()
    return [element[0] for element in result]

def get_auth_tokens(connection, selected_users):
    command = f'''
    SELECT userid, auth_token FROM Auth_info
        WHERE {format_OR_clause('userid', selected_users)};
    '''
    cursor = connection.cursor()
    cursor.execute(command)
    result = cursor.fetchall()
    return {data[0]: data[1] for data in result}

def get_refresh_tokens(connection, selected_users):
    command = f'''
    SELECT userid, refresh_token FROM auth_info
        WHERE {format_OR_clause('userid', selected_users)};
    '''
    cursor = connection.cursor()
    cursor.execute(command)
    result = cursor.fetchall()
    return {data[0]: data[1] for data in result}

#get data for a selected userid from a database
def get_data(connection, selected_user, datatype):
    command = f'''
    SELECT {datatype} FROM auth_info
        WHERE userid = "{selected_user}";
    '''
    cursor = connection.cursor()
    cursor.execute(command)
    result = cursor.fetchone()

    if result:
        return result[0]
    return False

def check_login_details(email, password, db):
    #navigate the database
    command = f"SELECT * FROM login_info WHERE email = '{email}'"
    cursor = db.cursor(dictionary=True) #allows us to access data by name
    cursor.execute(command)
    #if user exists, check if password is correct
    user_account = cursor.fetchone()
    if user_account:
        if checkpw(password.encode('utf-8'), user_account['password'].encode('utf-8')):
            return user_account
    return False

#Check if there is an available input key to register
def check_input_key(input_key, db):
    command = f"SELECT * FROM registration_keys WHERE user_key = '{input_key}' AND email IS NULL"
    cursor = db.cursor()
    cursor.execute(command)
    if cursor.fetchone():
        return True
    return False

#Check if device already exists and return a message to flash
def check_valid_device(user_id, patient_id, auth_db, db):
    #case 1 device already exists in auth_info
    command = f"SELECT * FROM auth_info WHERE userid = '{user_id}'"
    cursor = auth_db.cursor()
    cursor.execute(command)
    if cursor.fetchall():
        message = "Device Already Exists"
        return False, message

    #case 2 patient already exists in database
    command = f"SELECT * FROM patient_ids WHERE patient_id = '{patient_id}'"
    cursor = db.cursor()
    cursor.execute(command)
    if cursor.fetchall():
        message = "Please Choose Different Patient ID"
        return False, message
    return True, None

def check_patient_id(patient_id, device_db):
    #patient already exists in database
    if not isinstance(device_db, list):
        device_db = [device_db]
    for db in device_db:
        command = f"SELECT * FROM patient_ids WHERE patient_id = '{patient_id}'"
        cursor = db.cursor()
        cursor.execute(command)
        if cursor.fetchall():
            message = "Please Choose Different Patient ID"
            return False, message
    return True, None

def get_patient_id_from_user_id(user_id, device_db):
    cursor = device_db.cursor()
    cursor.execute(f"SELECT patient_id FROM patient_ids WHERE userid = '{user_id}'")
    patient = cursor.fetchone()
    if patient:
        return patient[0]
    return False

def get_last_update(user_id, device_db):
    cursor = device_db.cursor()
    cursor.execute(f"SELECT lastUpdate FROM devices WHERE userid = '{user_id}'")
    date_time = cursor.fetchall()
    if date_time:
        if isinstance(date_time[0], tuple):
            return date_time[0][0]
        return date_time[0]
    return False

#Get all current device users from the database
def get_device_users(db):
    cursor = db.cursor(dictionary=True)
    command = f'''
    SELECT * FROM patient_ids
    '''
    cursor.execute(command)
    result = cursor.fetchall()
    return result

def capitalize_first_letter(string):
    if string[0].isalpha():
        string = string[0].upper() + string[1:]
        return string
    else:
        return string

def email_exists(db, email):
    command = f"SELECT * FROM login_info WHERE email = '{email}'"
    cursor = db.cursor()
    cursor.execute(command)
    if cursor.fetchall():
        return True
    else:
        return False

def key_is_valid(db, key):
    command = f"SELECT * FROM registration_keys WHERE user_key = '{key}' AND email IS NULL"
    cursor = db.cursor()
    cursor.execute(command)
    if cursor.fetchall():
        return True
    else:
        return False

def format_OR_clause(column: str, condition: list):
        '''Input a column to query and a list of conditions. Output will be 
            a bunch of WHERE and OR clause
        Params
        ------
            column: str
            condition: list
        Returns
        -------
            WHERE_OR: str - WHERE column = condition1 OR column = condition2 OR column = condition3....  
        '''    
        where_clause = ''
        if len(condition) == 0:
            return where_clause

        where_clause += f"{column} = {condition[0]}"

        if len(condition) > 1:
            for i in range(1, len(condition)):
                where_clause += f" OR {column} = {condition[i]}"
        return where_clause

# if __name__ == "__main__":
#     db = connect_to_database('fitbit_2')
#     print(get_patient_id_from_user_id('BD6RKR', db))