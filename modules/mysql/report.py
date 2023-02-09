'''Functions to generate reports from the database'''
from bcrypt import checkpw
from modules.fitbit.authentication import get_fitbit_auth_info
from modules.withings.authentication import get_withings_auth_info
from modules.polar.authentication import get_polar_auth_info
from modules.mysql.setup import connect_to_database

def get_all_token_timeouts(connection):
    command = '''
    SELECT userid, expires_by FROM Auth_info;
    '''
    cursor = connection.cursor()
    cursor.execute(command)
    result = cursor.fetchall()
    return {data[0]: data[1] for data in result}

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
    cursor = db.cursor(dictionary=True) #allows us to access data by name
    cursor.execute(f"SELECT * FROM login_info WHERE email = '{email}'")
    #if user exists, check if password is correct
    user_account = cursor.fetchone()
    if user_account:
        if checkpw(password.encode('utf-8'), user_account['password'].encode('utf-8')):
            return user_account
    return False

#Check if there is an available input key to register
def check_input_key(input_key, db):
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM registration_keys WHERE user_key = '{input_key}' AND email IS NULL")
    if cursor.fetchall():
        return True
    return False

#Check if there is an available input key to register
def check_invalid_device(input_device, auth_db, fitbit_db):
    #case 1 device already exists is auth_info
    cursor = auth_db.cursor()
    cursor.execute(f"SELECT * FROM auth_info WHERE userid = '{input_device}'")
    if cursor.fetchall():
        return True

    #case 2 device already exists in fitbit database #todo: check for other databases
    cursor = fitbit_db.cursor()
    cursor.execute(f"SELECT * FROM patient_ids WHERE userid = '{input_device}'")
    if cursor.fetchall():
        return True

    return False


def check_auth_info_and_input_device(device_type, auth_db, device_db):
    auth_info = None
    print(device_type)
    if device_type == 'fitbit':
        auth_info = get_fitbit_auth_info()
    elif device_type == 'withings':
        auth_info = get_withings_auth_info()
    elif device_type == 'polar':
        auth_info = get_polar_auth_info()

    #check authentication info was received successfully
    if not auth_info:
        return "Authentication Failed", False

    #check if device is available
    user_id = auth_info['user_id']
    invalid_device = check_invalid_device(user_id, auth_db, device_db)
    if invalid_device:
       return "Device Already Exists", False

    return auth_info, True

#Get all current fitbit users from fitbit database
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

        where_clause += f'{column} = "{condition[0]}"'

        if len(condition) > 1:
            for i in range(1, len(condition)):
                where_clause += f" OR {column} = '{condition[i]}'"
        print(where_clause)
        return where_clause

if __name__ == "__main__":
    print(get_device_type(connect_to_database("authorization_info"), '33192922'))