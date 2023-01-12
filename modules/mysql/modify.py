'''Insert data into table'''
from sqlalchemy import create_engine
import pandas as pd
import pymysql

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
    REPLACE INTO patient_ids (userid, patientid)
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
    
def test_insertion():
    data_to_insert = [['user_id', 'patientid', 'device_type',
                       'access_token', 'refresh_token', '12345'], ]
    engine = create_engine(
        f'mysql+pymysql://writer:password@localhost/device_info')
    insert_list_into('patient_ids', data_to_insert, engine)

if __name__ == "__main__":
    test_insertion()
