'''The main application'''
import os
import sys
import numpy as np
import pandas as pd
from modules.mysql.setup import connect_to_database
from datetime import datetime, timedelta
from PyQt6.QtCore import QSize, Qt, QObject
from PyQt6.QtGui import QFont, QFontDatabase, QScreen, QGuiApplication, QColor, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QDateTimeEdit,
    QLabel,
    QStackedWidget,
    QComboBox,
    QRadioButton,
    QCheckBox,
    QSlider,
    QListWidget,
    QScrollBar,
    QListWidgetItem,
    QLineEdit,
    QTabWidget,
    QDateEdit,
    QPlainTextEdit,
    QGroupBox,
    QMessageBox,
    QGraphicsEffect,
    QGraphicsDropShadowEffect,
    QFrame,
    QInputDialog,
    QFormLayout
)
from superqt import QLabeledRangeSlider
from tkinter import filedialog
from pathlib import Path
from datetime import datetime, timedelta, timezone, date
import sys

import modules.fitbit.authentication as fitbit_auth
import modules.withings.authentication as withings_auth
import modules.fitbit.retrieve as fitbit_retrieve
import modules.withings.retrieve as withings_retrieve
import modules.mysql.report as report_db
import modules.mysql.modify as modify_db
import modules.mysql.setup as setup_db
from statistics import mean
from sqlalchemy import create_engine
import pprint as pp

try:
    import httplib  # python < 3.0
except:
    import http.client as httplib

import time


# NOTE: Add connection for new devices here! Make sure mysql databases already exist!!
fitbit_conn = create_engine(
    'mysql+pymysql://writer:password@localhost/fitbit')
withings_conn = create_engine(
    'mysql+pymysql://writer:password@localhost/withings')

# NOTE: Add new devices types here!
auth = {'fitbit': fitbit_auth,
        'withings': withings_auth}
retrieve = {'fitbit': fitbit_retrieve,
            'withings': withings_retrieve}
mysql_conn = {'fitbit': fitbit_conn,
              'withings': withings_conn}

# NOTE: Authorization Database name!
DATABASE = "authorization_info"

# ==================================================
# HELPER FUNCTIONS


def have_internet():
    conn = httplib.HTTPSConnection("8.8.8.8", timeout=5)
    try:
        conn.request("HEAD", "/")
        return True
    except Exception:
        return False
    finally:
        conn.close()

def flatten_dictionary(some_dict, parent_key='', separator='_'):
    flat_dict = {}
    for k, v in some_dict.items():
        new_key = parent_key + separator + k if parent_key else k
        new_key = new_key.replace(' ', '')
        if isinstance(v, list):
            continue  # v = dict([(x['name'], x) for x in v])
        if isinstance(v, dict):
            flat_dict.update(flatten_dictionary(v, parent_key=new_key))
        else:
            flat_dict[new_key] = v
    return flat_dict

def range_dates(startDate, endDate, step=1):
    for i in range((endDate-startDate).days):
        yield startDate + timedelta(days=step*i)

def create_drop_shadow(x, y, blur, color):
    dropshadow = QGraphicsDropShadowEffect()
    dropshadow.setBlurRadius(blur)
    dropshadow.setOffset(x, y)
    dropshadow.setColor(QColor(color))
    return dropshadow

def format_list_row(id, label):
    return '{:<30} {:}'.format(id, label)

# ==================================================


if getattr(sys, 'frozen', False):
    APPLICATION_PATH = Path(os.path.dirname(sys.executable))
    DATA_PATH = APPLICATION_PATH.joinpath('exported data')
elif __file__:
    APPLICATION_PATH = Path(os.path.dirname(
        __file__)).parent.resolve().parent.resolve()
    DATA_PATH = APPLICATION_PATH.joinpath('exported data')


# ==================================================
# MAIN APP

class MainWindow(QMainWindow):
    def __init__(self, resourcepath, db_path, screen_width, screen_height):
        super().__init__()
        self.stackedwidget = QStackedWidget()
        self.resourcepath = resourcepath
        self.db_path = db_path
        self.mysql_conn = connect_to_database(DATABASE)

        # make a mysql connection for each database (device)
        self.mysql_engine = {db: setup_db.make_engine(db) for db in auth.keys()}

        print(self.mysql_engine, '!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        self.screensize = (screen_width, screen_height)
        # print(self.screensize)

        self.setObjectName('bgApp')
        self.pageKeys = {'GetDataWindow': 0, 'Query': 1, 'Add Device': 2}

        self.wGetData = GetDataWindow(self)
        self.wGetData.setObjectName('getDataWindow')
        # self.wQuery = QueryWindow(self)
        # self.wInsert = InsertWindow(self)

        self.stackedwidget.addWidget(self.wGetData)
        self.stackedwidget.setCurrentIndex(0)

        self.setCentralWidget(self.stackedwidget)

    def center(self, screen):
        screen_center = screen.availableGeometry().center()
        app_rect = self.frameGeometry()
        app_rect.moveCenter(screen_center)
        self.move(app_rect.topLeft())


class GetDataWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()

        self.selectionLayout = QHBoxLayout()
        self.selectionLayout.setContentsMargins(30, 15, 30, 15)
        self.selectionLayout.setSpacing(30)

        # Declare the Widgets
        self.selectUsersWidget = QFrame()
        self.editUserLabelWidget = QFrame()
        self.selectDataTypeWidget = QFrame()
        self.selectDateRangeWidget = QFrame()
        self.exportDataButton = QPushButton('Export Data (MySQL + CSV)')
        self.doneMsgBox = QMessageBox()
        self.generalMsgBox = QMessageBox()

        # Configure the Widgets
        self.setupUserSelect()
        self.setupUserLabelEdit()
        self.setupDataSelect()
        self.setupDateRangeSelect()
        self.exportDataButton.clicked.connect(self.exportData)
        self.exportDataButton.setObjectName('exportDataButton')
        self.setupDoneMsgBox()

        # Arrange the Widgets
        self.layout.addLayout(self.selectionLayout)
        self.selectionLayout.addWidget(self.selectUsersWidget)
        self.selectionLayout.addWidget(self.selectDataTypeWidget)
        self.selectionLayout.addWidget(self.selectDateRangeWidget)
        self.selectionLayout.addWidget(self.exportDataButton)
        self.selectionLayout.addWidget(self.editUserLabelWidget)

        # Set the Layout
        self.setLayout(self.layout)

    # ==================================================
    # SETUP DISPLAY FUNCTIONS

    def setupUserSelect(self):
        layout = QVBoxLayout()
        self.selectUsersWidget.setObjectName('select-items')

        # Declare the Group's Widget
        title = QLabel('Select User IDs')

        all_devices = report_db.get_all_device_types(self.parent.mysql_conn)

        print(all_devices)
        listlabels = list(map(lambda x: format_list_row(*x), all_devices))

        self.userList = QUpdatableCheckBoxListWidget(self.addNewUser, listlabels)

        # Configure the Widgets
        title.setObjectName('group-title')
        # Arrange the widgets
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.userList)
        # Styling
        self.selectUsersWidget.setGraphicsEffect(
            create_drop_shadow(4, 4, 20, 'rgba(0,0,0,0.1)'))
        self.selectUsersWidget.setMinimumWidth(
            int(self.parent.screensize[0]*0.2))
        # Set the Parent Widget's Layout
        self.selectUsersWidget.setLayout(layout)

    def setupUserLabelEdit(self):
        layout = QVBoxLayout()
        self.editUserLabelWidget.setObjectName('select-items')

        # Declare the Group's Widget
        title = QLabel('Edit User Labels')

        all_devices = report_db.get_all_device_types(self.parent.mysql_conn)

        all_patientids = [(userid, modify_db.get_patientid(
            self.parent.mysql_engine[dev_type], userid)) for userid, dev_type in all_devices]

        all_items = [format_list_row(*x)
                     for x in all_patientids]

        self.labelList = QRadioButtonListWidget(
            self.editUserLabel, all_items)

        # Configure the Widgets
        title.setObjectName('group-title')
        # Arrange the widgets
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.labelList)
        # Styling
        self.editUserLabelWidget.setGraphicsEffect(
            create_drop_shadow(4, 4, 20, 'rgba(0,0,0,0.1)'))
        self.editUserLabelWidget.setMinimumWidth(
            int(self.parent.screensize[0]*0.2))
        # Set the Parent Widget's Layout
        self.editUserLabelWidget.setLayout(layout)

    def setupDataSelect(self):
        layout = QVBoxLayout()
        self.selectDataTypeWidget.setObjectName('select-items')

        # Declare the Widgets
        title = QLabel('Select Data Types')

        data_types = list(fitbit_retrieve.DataGetter('1111').api_map.keys(
        )) + list(withings_retrieve.DataGetter('1111').api_map.keys())

        self.dataTypeList = QCheckBoxListWidget(data_types)

        # Configure the Widgets
        title.setObjectName('group-title')
        self.dataTypeList.selectAllCheckbox.setChecked(False)
        # Arrange the Widgets
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.dataTypeList)
        # Styling
        self.selectDataTypeWidget.setGraphicsEffect(
            create_drop_shadow(4, 4, 20, 'rgba(0,0,0,0.1)'))
        self.selectDataTypeWidget.setMinimumWidth(
            int(self.parent.screensize[0]*0.2))
        # Set the Parent Widget's Layout
        self.selectDataTypeWidget.setLayout(layout)

    def setupDateRangeSelect(self):
        layout = QVBoxLayout()
        self.selectDateRangeWidget.setObjectName('select-items')

        # Declare the Widgets
        title = QLabel('Select Date Range')
        startDateLabel = QLabel('Start Date')
        endDateLabel = QLabel('End Date')
        self.startDate = QDateEdit()
        self.endDate = QDateEdit()
        dummyLabel = QLabel('')
        # Configure the Widgets
        title.setObjectName('group-title')
        self.startDate.setCalendarPopup(True)
        self.startDate.setDate((datetime.now()-timedelta(days=30)).date())
        self.startDate.dateChanged.connect(self.handleChangeStartDate)
        self.endDate.setDate(datetime.now().date())
        self.endDate.setCalendarPopup(True)
        self.endDate.dateChanged.connect(self.handleChangeEndDate)
        self.endDate.setMaximumDate(datetime.now().date())
        self.endDate.setMinimumDate((datetime.now()-timedelta(days=29)).date())
        # Arrange the Widgets
        layout.addWidget(
            title, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(startDateLabel, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.startDate, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(endDateLabel, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.endDate, alignment=Qt.AlignmentFlag.AlignTop)
        # Add this so the date range select boxes don't stretch weirdly
        layout.addWidget(dummyLabel, 2)
        # Styling
        self.selectDateRangeWidget.setGraphicsEffect(
            create_drop_shadow(4, 4, 20, 'rgba(0,0,0,0.5)'))
        # Set the Parent Widget's Layout
        self.selectDateRangeWidget.setLayout(layout)

    def setupDoneMsgBox(self):
        # Configure the Widget
        self.doneMsgBox.setWindowTitle('Done!')
        self.doneMsgBox.setText('Export Done! Thanks for Waiting')
        self.doneMsgBox.setIcon(QMessageBox.Icon.Information)

    # ==================================================
    def handleChangeEndDate(self):
        # Reset the completed labels on the userList. Only include here because EndDate gets changed in StartDate (causing recursion if we put in both)
        self.userList.reset_checkbox_labels()

    def handleChangeStartDate(self, value):
        # Modify the maximum and minimum of the enddate (enddate will automatically adjust if out of range)
        self.endDate.setMaximumDate((datetime.combine(
            value.toPyDate(), datetime.min.time())+timedelta(days=30)).date())
        self.endDate.setMinimumDate((datetime.combine(
            value.toPyDate(), datetime.min.time())+timedelta(days=1)).date())

    def editUserLabel(self):
        '''edit the label (patient id) of the selected user'''
        items = self.labelList.get_checked_items()  # list of 0 or 1 QRadioButton objects
        if not items:
            print('no user selected!')
            return
        
        print(items)
        userid = items[0].text().split()[0]

        print(userid, '!!!!!!!!!!!!!!!!!!!!!!!!!!')
        patientid, ok = QInputDialog.getText(
            self, 'enter new patient id', 'enter string (no spaces!):')
        
        if ok and patientid:
            if ' ' in patientid:
                print('bad patient id')
                return
            dtype = report_db.get_device_types(self.parent.mysql_conn, ['\"'+userid+'\"'])[userid]
            print(dtype, '!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            modify_db.update_patientid(self.parent.mysql_engine[dtype], userid, patientid)

            # update list widget
            items[0].setText(format_list_row(userid, patientid))
        
    def addNewUser(self):

        # get device type (e.g. fitbit, withings, etc)
        items = list(auth.keys())   # all device types
        device_type, ok = QInputDialog.getItem(self, "select device type",
                                      "choose one:", items, 0, False)

        if ok and device_type:
            auth_info = auth[device_type].get_auth_info()

            if auth_info == '':
                print('Couldn\'t get the new auth_info')
                return ''

            expires_by = int((datetime.now() + timedelta(seconds=auth_info['expires_in'])).replace(tzinfo=timezone.utc).timestamp())
            data_to_insert = [[auth_info['user_id'], device_type,
                            auth_info['access_token'], auth_info['refresh_token'], expires_by], ]

            try:
                modify_db.insert_list_into(
                    'Auth_info', data_to_insert, self.parent.mysql_conn)
                return format_list_row(auth_info['user_id'], device_type)
            except Exception as e:
                print(e)
        return ''

    def exportData(self):
        '''Grab the users, the data types, the date range'''

        output_path = DATA_PATH.joinpath(
            f'{datetime.now().strftime("%Y-%m-%d %H.%M.%S")}')

        query_selected_userids = list(
            map(lambda text: f'\'{text.split()[0]}\'', self.userList.get_checked_items()))
        access_tokens = report_db.get_auth_tokens(
            self.parent.mysql_conn, query_selected_userids)
        refresh_tokens = report_db.get_refresh_tokens(
            self.parent.mysql_conn, query_selected_userids)
        device_types = report_db.get_device_types(
            self.parent.mysql_conn, query_selected_userids)

        print(query_selected_userids)

        # normal selected_userids
        selected_datatypes = self.dataTypeList.get_checked_items()

        startDate = self.startDate.date().toString('yyyy-MM-dd')
        endDate = self.endDate.date().toString('yyyy-MM-dd')

        request_num = 0
        start_time = time.time()
        for userid, device_type in device_types.items():

            errorFlag = False

            print(userid, device_type)
            if device_type not in auth.keys():
                self.userList.checkboxes[userid].setText(
                    f'X {userid} ERROR: Unknown Device Type')
                self.userList.checkboxes[userid].setStyleSheet('color: red')
                errorFlag = True
                continue

            UserDataRetriever = retrieve[device_type].DataGetter(access_tokens[userid])

            for data_type in selected_datatypes:

                if data_type not in UserDataRetriever.api_map:
                    continue    # data type for a different device
                print(data_type, startDate, endDate)

                result = UserDataRetriever.api_map[data_type](
                    startDate, endDate)

                print('result:', result)
                print('result.status_code: ', result.status_code)

                data = result.json()
                print('data:', data)

                # TODO: clean up and further test this "if" statement
                if result.status_code == 401 or ('status' in data and data['status'] == 401):
                    # Expired token
                    new_auth_info = auth[device_type].get_refreshed_auth_info(
                        userid, refresh_tokens[userid])

                    print('new_auth_info:', new_auth_info)
                    # Bad Refresh Token
                    if new_auth_info == 400:
                        self.generalMsgBox.setText(
                            f'Bad refresh token, enter credentials for userid: {userid}')
                        self.generalMsgBox.setIcon(
                            QMessageBox.Icon.Information)
                        self.generalMsgBox.exec()
                        new_auth_info = auth[device_type].get_auth_info()

                    # If There is a problem with getting new auth info, skip
                    if new_auth_info == '':
                        self.userList.checkboxes[userid].setText(
                            f'X {userid} ERROR: Could not get Access Token')
                        self.userList.checkboxes[userid].setStyleSheet(
                            'color: red')
                        errorFlag = True
                        break

                    # Update the database
                    modify_db.update_auth_token(
                        self.parent.mysql_conn, userid, new_auth_info['access_token'])
                    modify_db.update_refresh_token(
                        self.parent.mysql_conn, userid, new_auth_info['refresh_token'])

                    # Update the retriever
                    UserDataRetriever.token = new_auth_info['access_token']

                    # Try the request again
                    result = UserDataRetriever.api_map[data_type](
                        startDate, endDate)

                print('data_type', data_type)
                # Get the data. If intraday, it is the first date
                data = result.json()

                if data == '':
                    continue    # no data

                if device_type == 'withings' and 'body' in data:
                    data = data['body']
                    if 'series' in data:
                        data[data_type] = data.pop('series')

                        for i, val in enumerate(data[data_type]):
                            data[data_type][i]['hr'] = mean(val['hr'].values())
                            data[data_type][i]['rr'] = mean(val['rr'].values())
                            data[data_type][i]['snoring'] = mean(
                                val['snoring'].values())

                request_num += 1
                # Most likely too many request error here:
                if device_type == 'fitbit' and type(data) is dict:
                    if 'errors' in list(data.keys()):
                        self.userList.checkboxes[userid].setText(
                            f'X {userid} ERROR: Too many Requests')
                        self.userList.checkboxes[userid].setStyleSheet(
                            'color: red')
                        errorFlag = True
                        break

                    # Get the first list
                    for key in data_type.split(' '):
                        data = data[key]

                    # Handle Intraday - selection includes 'dataset'... since intraday can only grab one day
                    if len(data_type.split(' ')) > 1 and data_type.split(' ')[1] == 'dataset':
                        data = []
                        intraday_dates = list(range_dates(datetime.strptime(
                            startDate, '%Y-%m-%d').date(), datetime.strptime(endDate, '%Y-%m-%d').date()))
                        for one_date in intraday_dates:
                            # Grab the result for the next date
                            result = UserDataRetriever.api_map[data_type](
                                str(one_date), endDate)  # Since one_date is a datetime.date
                            next_day_data = result.json()

                            # Fitbit only returns the time so format it into a datetime
                            for key in data_type.split(' '):
                                next_day_data = next_day_data[key]
                            # Format time to datetime
                            next_day_data = [{'datetime': datetime.strptime(
                                f"{str(one_date)} {data['time']}", "%Y-%m-%d %H:%M:%S"), 'value': data['value']} for data in next_day_data]
                            # There should only be a list left
                            data += next_day_data
                            request_num += 1

                print('result: ', data)
                # Data is sometimes weirdly formatted with nested dictionaries. Flatten the data
                data_type = data_type.replace(' dataset', '')
                if isinstance(data, dict):
                    data = [flatten_dictionary(
                        d) for d in data[data_type]]

                assert(isinstance(data, list))

                if len(data):
                    df = pd.DataFrame(data)
                    df['userid'] = userid

                    pp.pprint(df.head())
                    print(df.info())

                    # Make the export path
                    output_path.mkdir(parents=True, exist_ok=True)
                    # Export to .csv
                    df.to_csv(output_path.joinpath(
                        f'{userid}_{data_type}_{startDate}_{endDate}.csv'), index=False)
                    
                    # Write dataframe to mysql table
                    table = data_type.replace('-', '').replace(' dataset', '')
                    df.to_sql(con=mysql_conn[device_type], name=table,
                              if_exists='append', index=False)

            # Turn the Userid Green Once the Export is done
            if not errorFlag:  # Because we break out of the loop
                index = format_list_row(userid, device_type)
                self.userList.checkboxes[index].setText(f'✓ {index}')
                self.userList.checkboxes[index].setStyleSheet('color: green')

        print(f'Time Elapsed for {request_num} requests = {time.time()-start_time}')

        # Show that the export is done
        self.doneMsgBox.setText(
            f'Export done! Successful exports can be found at:\n {output_path}')
        self.doneMsgBox.exec()

class QRadioButtonListWidget(QWidget):
    '''A listwidget with radio buttons.'''
    def __init__(self, edit_item, item_names=[]):
        super().__init__()

        self.layout = QVBoxLayout()
        self.rbuttons = {item_name: None for item_name in item_names}

        # Declare the Widgets
        self.editLabelButton = QPushButton('Edit Patient Label')
        self.rbuttonList = QListWidget()

        # Configure the Widgets
        self.editLabelButton.clicked.connect(edit_item)
        self.rbuttonList.setSpacing(3)

        # Populate the radiobuttons
        for item_name in self.rbuttons:
            self.rbuttons[item_name] = QRadioButton(item_name)
            self.rbuttons[item_name].setChecked(False)

        # Add the radiobuttons to the listwidget
        for item_name in self.rbuttons:
            listwidgetItem = QListWidgetItem()
            self.rbuttonList.addItem(listwidgetItem)
            self.rbuttonList.setItemWidget(
                listwidgetItem, self.rbuttons[item_name])

        # Arrange the Widgets
        self.layout.addWidget(
            self.editLabelButton, alignment=Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.rbuttonList)

        # Set the Layout
        self.setLayout(self.layout)

    def get_checked_items(self):
        # returns a list of selected QRadioButton objects (at most one button can be selected)
        return [self.rbuttons[item_name] for item_name in self.rbuttons if self.rbuttons[item_name].isChecked()]

    def editItem(self, item_name):
        for item in self.rbuttonList:
            if item.isChecked():            # find single checked box
                item.setText(item_name)

class QCheckBoxListWidget(QWidget):
    '''A listwidget with checkboxes. Includes a select all button as well'''
    def __init__(self, item_names=[]):
        super().__init__()

        self.layout = QVBoxLayout()
        self.checkboxes = {item_name: None for item_name in item_names}

        # Declare the Widgets
        self.selectAllCheckbox = QCheckBox('Select All')
        self.checkboxList = QListWidget()

        # Configure the Widgets
        self.checkboxList.setSpacing(3)
        self.selectAllCheckbox.setChecked(True)
        self.selectAllCheckbox.stateChanged.connect(self.handleSelectAllToggle)

        # Populate the checkboxes  
        for item_name in self.checkboxes:
            self.checkboxes[item_name] = QCheckBox(item_name)
            self.checkboxes[item_name].setChecked(True)

        # Add the checkboxes to the listwidget
        for item_name in self.checkboxes:
            listwidgetItem = QListWidgetItem()
            self.checkboxList.addItem(listwidgetItem)
            self.checkboxList.setItemWidget(listwidgetItem, self.checkboxes[item_name])
        
        # Arrange the Widgets
        self.layout.addWidget(self.selectAllCheckbox)
        self.layout.addWidget(self.checkboxList)

        # Set the Layout
        self.setLayout(self.layout)

    def handleSelectAllToggle(self, value):
        if value == 0:
            for item_name in self.checkboxes:
                self.checkboxes[item_name].setChecked(False)
        else:
            for item_name in self.checkboxes:
                self.checkboxes[item_name].setChecked(True)
        
    def get_checked_items(self):
        return [item_name for item_name in self.checkboxes if self.checkboxes[item_name].isChecked()]

    def reset_checkbox_labels(self):
        for key in self.checkboxes:
            self.checkboxes[key].setText(key)
            self.checkboxes[key].setStyleSheet('color: white')

class QUpdatableCheckBoxListWidget(QCheckBoxListWidget):
    def __init__(self, get_new_item, item_names=[]):
        super().__init__(item_names)
        self.clearLayoutWidgets(self.layout)
        self.menuLayout = QVBoxLayout()

        # Declare the Widgets
        self.addDeviceButton = QPushButton('Add New Device')

        # Configure the widgets
        self.addDeviceButton.clicked.connect(
            lambda: self.addItem(get_new_item()))

        # Arrange the Widgets
        self.menuLayout.addWidget(self.selectAllCheckbox)
        self.menuLayout.addWidget(
            self.addDeviceButton, alignment=Qt.AlignmentFlag.AlignRight)

        self.layout.addLayout(self.menuLayout)
        self.layout.addWidget(self.checkboxList)

        # Set the layout
        self.setLayout(self.layout)

    def clearLayoutWidgets(self, layout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)

    def addItem(self, item_name):
        # Update the dict so that the new item goes first
        if item_name not in list(self.checkboxes.keys()) and item_name != '':
            new_dict = {item_name: QCheckBox(item_name)}
            new_dict.update(self.checkboxes)
            self.checkboxes = new_dict
            self.checkboxes[item_name].setChecked(True)
            listwidgetItem = QListWidgetItem()
            self.checkboxList.insertItem(0, listwidgetItem)
            self.checkboxList.setItemWidget(
                listwidgetItem, self.checkboxes[item_name])
        else:
            print('Already added or Nothing Inputted')
            return

# ==================================================
# ==================================================
def run(resourcepath, db_path):
    app = QApplication(sys.argv)
    connectMsgBox = QMessageBox()
    connectMsgBox.setText(
        'There is no internet connection. Please check your Internet Connection.')
    connectMsgBox.setIcon(QMessageBox.Icon.Critical)
    if have_internet():
        screen = app.screens()[0]
        window = MainWindow(resourcepath, db_path, screen.availableGeometry(
        ).width(), screen.availableGeometry().height())
        for font_path in Path(resourcepath).joinpath('fonts').glob('*.ttf'):
            QFontDatabase.addApplicationFont(str(font_path))
        arrow_path = str(Path(resourcepath).joinpath(
            'images', 'icons', 'cil-arrow-bottom.png')).replace('\\', '/')
        # overall_font_size = int(round(20/1824*window.screensize[1]))
        # title_font_size = overall_font_size + 4
        # fieldlabel_font_size = overall_font_size - 2
        # visualizationtitle_font_size = overall_font_size +3
        window.show()
        window.center(screen)
        stylesheet = (open(str(Path(resourcepath).joinpath(
            'themes', 'path_theme.qss')), "r").read() % (arrow_path))
        window.setStyleSheet(stylesheet)
        window.setWindowIcon(QIcon(str(Path(resourcepath).joinpath(
            'images', 'icons', 'favicon.ico')).replace('\\', '/')))
        window.setWindowTitle('PATH - Fitbit Extractor')
        app.exec()
    else:
        connectMsgBox.exec()
