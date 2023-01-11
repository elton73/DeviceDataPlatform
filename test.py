import mysql.connector
from sqlalchemy import create_engine
from pathlib import Path
import pymysql
import sys
import os
import modules.mysql.report as mysql_report_db
import modules.mysql.modify as mysql_modify_db
import modules.mysql.setup as mysql_setup_db
from PyQt6.QtWidgets import QWidget
import modules.fitbit.authentication as fitbit_auth
import modules.withings.authentication as withings_auth


def get_patient_id(con, userid):
    command = f'''
    SELECT userid
    FROM auth_info
    WHERE userid = '{userid}';
    '''
    rs = con.execute(command)
    id_list = list(rs)
    return id_list[0][0] if id_list else ''

if __name__ == '__main__':
    database = mysql.connector.connect(
        host='localhost',
        user='root',
        passwd='password',
        database='devices'
    )

    mycursor = database.cursor()


    auth = {'fitbit': fitbit_auth,
        'withings': withings_auth}

    mysql_engine = create_engine("mysql://root:password@localhost:3306/devices")

    con = mysql_engine.connect()

    all_devices = mysql_report_db.get_all_device_types(database)
    
    for userid, dev_type in all_devices:
        all_patientids = (userid, get_patient_id(mysql_engine, userid))

    print(all_patientids)
   


    # mysql_engine = create_engine("mysql://root:rootuser@localhost:3306/devices")



    """ TRANSFERRING SQLITE TABLE TO MYSQL """
    # mycursor.execute("CREATE DATABASE devices")
    # mycursor.execute("CREATE TABLE device_info (userid VARCHAR(50) PRIMARY KEY, device_type VARCHAR(50), auth_token VARCHAR(500), refresh_token VARCHAR(500), expires_by VARCHAR(100))")
    # mycursor.execute("DROP TABLE device_info")
    # mycursor.execute("ALTER TABLE device_info RENAME auth_info")
    # db.commit()

    # conn = sqlite3.connect('db.sqlite3')
    # cursor = conn.cursor()
    # cursor.execute("SELECT * FROM Auth_info")
    # list1 = cursor.fetchall()[1]

    # mycursor.execute("INSERT INTO device_info (userid, device_type, auth_token, refresh_token, expires_by) VALUES (%s ,%s ,%s ,%s, %s)", (list1[0], list1[1], list1[2], list1[3], list1[4]))
    # db.commit()


