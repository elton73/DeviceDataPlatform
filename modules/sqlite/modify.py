'''Insert data into table'''


def insert_list_into(table: str, items: list, connection, label_exists=False):
    cursor = connection.cursor()
    print(f'SELECT * FROM {table}')
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

