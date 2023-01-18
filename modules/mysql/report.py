'''Functions to generate reports from the database'''
from bcrypt import checkpw
from modules.mysql.setup import connect_to_database, connect_to_server

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
    SELECT userid, refresh_token FROM Auth_info
        WHERE {format_OR_clause('userid', selected_users)};
    '''
    cursor = connection.cursor()
    cursor.execute(command)
    result = cursor.fetchall()
    return {data[0]: data[1] for data in result}


def get_device_types(connection, selected_users):
    command = f'''
    SELECT userid, device_type FROM Auth_info
        WHERE {format_OR_clause('userid', selected_users)};
    '''
    cursor = connection.cursor()
    print(command)
    cursor.execute(command)
    result = cursor.fetchall()
    return {data[0]: data[1] for data in result}

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
def check_input_device(input_device):
    #case 1 device already exists is auth_info
    invalid_device = False
    db = connect_to_database("authorization_info")
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM auth_info WHERE userid = '{input_device}'")
    if cursor.fetchall():
        return True

    #case 2 device already exists in patient_labels
    db2 = connect_to_database("patient_labels")
    cursor2 = db2.cursor()
    cursor2.execute(f"SELECT * FROM patient_label WHERE userid = '{input_device}'")
    if cursor2.fetchall():
        return True

    return False

def get_all_device_types(connection):
    command = f'''
    SELECT userid, device_type FROM auth_info;
    '''
    cursor = connection.cursor(dictionary=True)
    cursor.execute(command)
    result = cursor.fetchall()
    return result

def get_all_patient_labels(db):
    command = f'''
    SELECT * FROM patient_label;
    '''
    cursor = db.cursor(dictionary=True)
    cursor.execute(command)
    result = cursor.fetchall()
    return result

#Get all current fitbit users
def get_fitbit_users():
    server = connect_to_server()
    cursor = server.cursor()
    command = f'''
    SELECT patientid FROM fitbit.patient_ids WHERE userid IN 
   (SELECT userid FROM authorization_info.auth_info)
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

        where_clause += f'{column} = {condition[0]}'

        if len(condition) > 1:
            for i in range(1, len(condition)):
                where_clause += f' OR {column} = {condition[i]}'
        
        return where_clause

# if __name__ == '__main__':
#     db = connect_to_database("authorization_info")
#     db2 = connect_to_database("fitbit")
#     print(get_all_device_types(db))
