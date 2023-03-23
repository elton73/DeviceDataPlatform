'''The main application'''
import os
import sys
import numpy as np
import pandas as pd
from modules.mysql.setup import connect_to_database
from modules.fitbit.authentication import get_fitbit_auth_info as get_auth_info, get_refreshed_fitbit_auth_info
from modules import AUTH_DATABASE, FITBIT_DATABASE, FITBIT_ENGINE
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

try:
    import httplib  # python < 3.0
except:
    import http.client as httplib

import time

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
    for i in range((endDate - startDate).days):
        yield startDate + timedelta(days=step * i)


def create_drop_shadow(x, y, blur, color):
    dropshadow = QGraphicsDropShadowEffect()
    dropshadow.setBlurRadius(blur)
    dropshadow.setOffset(x, y)
    dropshadow.setColor(QColor(color))
    return dropshadow


# ==================================================

if getattr(sys, 'frozen', False):
    APPLICATION_PATH = Path(os.path.dirname(sys.executable))
    DATA_PATH = APPLICATION_PATH.joinpath('exported data')
elif __file__:
    APPLICATION_PATH = Path(os.path.dirname(__file__)).parent.resolve().parent.resolve()
    DATA_PATH = APPLICATION_PATH.joinpath('exported data')


# ==================================================
# MAIN APP

class MainWindow(QMainWindow):
    def __init__(self, resourcepath, db_path, screen_width, screen_height):
        super().__init__()
        self.stackedwidget = QStackedWidget()
        self.resourcepath = resourcepath
        self.db_path = db_path
        self.mysql_conn = connect_to_database(AUTH_DATABASE)
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
        self.selectDataTypeWidget = QFrame()
        self.selectDateRangeWidget = QFrame()
        self.exportDataButton = QPushButton('Export Data')
        self.writeDataButton = QPushButton('Write Data (MySQL)')
        self.doneMsgBox = QMessageBox()
        self.generalMsgBox = QMessageBox()

        # Configure the Widgets
        self.setupUserSelect()
        self.setupDataSelect()
        self.setupDateRangeSelect()
        self.exportDataButton.clicked.connect(self.exportCSVData)
        self.exportDataButton.setObjectName('exportDataButton')
        self.writeDataButton.clicked.connect(self.writeSQLData)
        self.writeDataButton.setObjectName('writeDataButton')
        self.setupDoneMsgBox()

        # Arrange the Widgets
        self.layout.addLayout(self.selectionLayout)
        self.selectionLayout.addWidget(self.selectUsersWidget)
        self.selectionLayout.addWidget(self.selectDataTypeWidget)
        self.selectionLayout.addWidget(self.selectDateRangeWidget)
        self.selectionLayout.addWidget(self.exportDataButton)
        self.selectionLayout.addWidget(self.writeDataButton)

        # Set the Layout
        self.setLayout(self.layout)

    # ==================================================
    # SETUP DISPLAY FUNCTIONS

    def setupUserSelect(self):
        layout = QVBoxLayout()
        self.selectUsersWidget.setObjectName('select-items')

        # Declare the Group's Widget
        title = QLabel('Select User IDs')
        self.userList = QUpdatableCheckBoxListWidget(self.addNewUser, report_db.get_all_user_ids(self.parent.mysql_conn),
                                                     'Add New User')
        # Configure the Widgets
        title.setObjectName('group-title')
        # Arrange the widgets
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.userList)
        # Styling
        self.selectUsersWidget.setGraphicsEffect(create_drop_shadow(4, 4, 20, 'rgba(0,0,0,0.1)'))
        self.selectUsersWidget.setMinimumWidth(int(self.parent.screensize[0] * 0.2))
        # Set the Parent Widget's Layout
        self.selectUsersWidget.setLayout(layout)

    def setupDataSelect(self):
        layout = QVBoxLayout()
        self.selectDataTypeWidget.setObjectName('select-items')

        # Declare the Widgets
        title = QLabel('Select Data Types')
        self.dataTypeList = QCheckBoxListWidget(list(fitbit_retrieve.DataGetter('1111').api_map.keys()))
        # Configure the Widgets
        title.setObjectName('group-title')
        self.dataTypeList.selectAllCheckbox.setChecked(False)
        # Arrange the Widgets
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.dataTypeList)
        # Styling
        self.selectDataTypeWidget.setGraphicsEffect(create_drop_shadow(4, 4, 20, 'rgba(0,0,0,0.1)'))
        self.selectDataTypeWidget.setMinimumWidth(int(self.parent.screensize[0] * 0.2))
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
        self.startDate.setDate((datetime.now() - timedelta(days=30)).date())
        self.startDate.dateChanged.connect(self.handleChangeStartDate)
        self.endDate.setDate(datetime.now().date())
        self.endDate.setCalendarPopup(True)
        self.endDate.dateChanged.connect(self.handleChangeEndDate)
        self.endDate.setMaximumDate(datetime.now().date())
        self.endDate.setMinimumDate((datetime.now() - timedelta(days=29)).date())
        # Arrange the Widgets
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(startDateLabel, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.startDate, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(endDateLabel, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.endDate, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(dummyLabel, 2)  # Add this so the date range select boxes don't stretch weirdly
        # Styling
        self.selectDateRangeWidget.setGraphicsEffect(create_drop_shadow(4, 4, 20, 'rgba(0,0,0,0.5)'))
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
        self.endDate.setMaximumDate(
            (datetime.combine(value.toPyDate(), datetime.min.time()) + timedelta(days=30)).date())
        self.endDate.setMinimumDate(
            (datetime.combine(value.toPyDate(), datetime.min.time()) + timedelta(days=1)).date())

    def addNewUser(self):
        auth_info = get_auth_info()
        if auth_info == '':
            print('Couldn\'t get the new auth_info')
            return ''

        expires_by = int(
            (datetime.now() + timedelta(seconds=auth_info['expires_in'])).replace(tzinfo=timezone.utc).timestamp())
        data_to_insert = [[auth_info['user_id'], auth_info['access_token'], auth_info['refresh_token'], expires_by], ]

        try:
            modify_db.insert_list_into('Auth_info', data_to_insert, self.parent.mysql_conn)
            return auth_info['user_id']
        except Exception as e:
            print(e)
            return ''

    def writeSQLData(self):
        '''Grab the users, the data types, the date range'''
        # output_path = DATA_PATH.joinpath(f'{datetime.now().strftime("%Y-%m-%d %H.%M.%S")}')
        # print(f"Exporting Data to {output_path}")

        print("pressed new button!!!")

        # Selected user IDs must be wrapped with single quotes for SQLite Query
        query_selected_userids = list(map(lambda text: f'\'{text}\'', self.userList.get_checked_items()))
        access_tokens = report_db.get_auth_tokens(self.parent.mysql_conn, query_selected_userids)
        refresh_tokens = report_db.get_refresh_tokens(self.parent.mysql_conn, query_selected_userids)
        # normal selected_userids
        selected_userids = self.userList.get_checked_items()
        selectedDataTypes = self.dataTypeList.get_checked_items()
        # startDate = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')         # yesterday
        # endDate = datetime.now().strftime('%Y-%m-%d')                               # today

        startDate = self.startDate.date().toString('yyyy-MM-dd')
        endDate = self.endDate.date().toString('yyyy-MM-dd')

        conn = FITBIT_ENGINE

        request_num = 0
        start_time = time.time()
        for userid in selected_userids:

            errorFlag = False
            UserDataRetriever = fitbit_retrieve.DataGetter(access_tokens[userid])
            for dataType in selectedDataTypes:
                print(dataType, startDate, endDate)
                result = UserDataRetriever.api_map[dataType](startDate, endDate)
                if result.status_code == 401:
                    # Expired token
                    new_auth_info = get_refreshed_fitbit_auth_info(userid, refresh_tokens[userid])

                    # Bad Refresh Token
                    if new_auth_info == 400:
                        self.generalMsgBox.setText(f'Bad refresh token, enter credentials for userid: {userid}')
                        self.generalMsgBox.setIcon(QMessageBox.Icon.Information)
                        self.generalMsgBox.exec()
                        new_auth_info = get_auth_info()

                    # If There is a problem with getting new auth info, skip
                    if new_auth_info == '':
                        self.userList.checkboxes[userid].setText(f'X {userid} ERROR: Could not get Access Token')
                        self.userList.checkboxes[userid].setStyleSheet('color: red')
                        errorFlag = True
                        break

                    # Update the database
                    modify_db.update_auth_token(self.parent.mysql_conn, userid, new_auth_info['access_token'])
                    modify_db.update_refresh_token(self.parent.mysql_conn, userid, new_auth_info['refresh_token'])
                    # Update the retriever
                    UserDataRetriever.token = new_auth_info['access_token']
                    # Try the request again

                    print(startDate, endDate)
                    result = UserDataRetriever.api_map[dataType](startDate, endDate)

                print('dataType', dataType)
                # Get the data. If intraday, it is the first date
                data = result.json()

                print(data)
                request_num += 1
                # Most likely too many request error here:

                if type(data) is dict:
                    if 'errors' in list(data.keys()):
                        self.userList.checkboxes[userid].setText(f'X {userid} ERROR: Too many Requests')
                        self.userList.checkboxes[userid].setStyleSheet('color: red')
                        errorFlag = True
                        break

                    # Get the first list
                    for key in dataType.split(' '):
                        data = data[key]

                        # Handle Intraday - selection includes 'dataset'... since intraday can only grab one day
                    if len(dataType.split(' ')) > 1 and dataType.split(' ')[1] == 'dataset':
                        data = []
                        intraday_dates = list(range_dates(datetime.strptime(startDate, '%Y-%m-%d').date(),
                                                          datetime.strptime(endDate, '%Y-%m-%d').date()))
                        for one_date in intraday_dates:
                            # Grab the result for the next date
                            result = UserDataRetriever.api_map[dataType](str(one_date),
                                                                         endDate)  # Since one_date is a datetime.date
                            next_day_data = result.json()

                            # Fitbit only returns the time so format it into a datetime

                            for key in dataType.split(' '):
                                next_day_data = next_day_data[key]
                            # Format time to datetime
                            next_day_data = [
                                {'datetime': datetime.strptime(f"{str(one_date)} {data['time']}", "%Y-%m-%d %H:%M:%S"),
                                 'value': data['value']} for data in next_day_data]
                            # There should only be a list left
                            data += next_day_data
                            request_num += 1

                # Data is sometimes weirdly formatted with nested dictionaries. Flatten the data
                # data = [flatten_dictionary(d) for d in data]
                # Format the data as a dataframe

                if len(data):
                    print(data[0])

                    data = [flatten_dictionary(d) for d in data]
                    print('data: ', data)
                    df = pd.DataFrame(data)
                    df['userid'] = userid

                    print(df.head())
                    print(df.info())

                    table = dataType.replace('-', '').replace(' dataset', '')
                    df.to_sql(con=conn, name=table, if_exists='append')

            # Turn the Userid Green Once the Export is done
            if not errorFlag:  # Because we break out of the loop
                self.userList.checkboxes[userid].setText(f'✓ {userid}')
                self.userList.checkboxes[userid].setStyleSheet('color: green')

        print(f'Time Elapsed for {request_num} requests = {time.time() - start_time}')

    def exportCSVData(self):
        '''Grab the users, the data types, the date range'''
        output_path = DATA_PATH.joinpath(f'{datetime.now().strftime("%Y-%m-%d %H.%M.%S")}')
        # print(f"Exporting Data to {output_path}")

        # Selected user IDs must be wrapped with single quotes for SQLite Query
        query_selected_userids = list(map(lambda text: f'\'{text}\'', self.userList.get_checked_items()))
        access_tokens = report_db.get_auth_tokens(self.parent.mysql_conn, query_selected_userids)
        refresh_tokens = report_db.get_refresh_tokens(self.parent.mysql_conn, query_selected_userids)
        # normal selected_userids
        selected_userids = self.userList.get_checked_items()
        selectedDataTypes = self.dataTypeList.get_checked_items()
        startDate = self.startDate.date().toString('yyyy-MM-dd')
        endDate = self.endDate.date().toString('yyyy-MM-dd')

        request_num = 0
        start_time = time.time()
        for userid in selected_userids:

            errorFlag = False
            UserDataRetriever = fitbit_retrieve.DataGetter(access_tokens[userid])
            for dataType in selectedDataTypes:
                print(dataType, startDate, endDate)
                result = UserDataRetriever.api_map[dataType](startDate, endDate)
                if result.status_code == 401:
                    # Expired token
                    new_auth_info = get_refreshed_fitbit_auth_info(userid, refresh_tokens[userid])

                    # Bad Refresh Token
                    if new_auth_info == 400:
                        self.generalMsgBox.setText(f'Bad refresh token, enter credentials for userid: {userid}')
                        self.generalMsgBox.setIcon(QMessageBox.Icon.Information)
                        self.generalMsgBox.exec()
                        new_auth_info = get_auth_info()

                    # If There is a problem with getting new auth info, skip
                    if new_auth_info == '':
                        self.userList.checkboxes[userid].setText(f'X {userid} ERROR: Could not get Access Token')
                        self.userList.checkboxes[userid].setStyleSheet('color: red')
                        errorFlag = True
                        break

                    # Update the database
                    modify_db.update_auth_token(self.parent.mysql_conn, userid, new_auth_info['access_token'])
                    modify_db.update_refresh_token(self.parent.mysql_conn, userid, new_auth_info['refresh_token'])
                    # Update the retriever
                    UserDataRetriever.token = new_auth_info['access_token']
                    # Try the request again
                    result = UserDataRetriever.api_map[dataType](startDate, endDate)

                # Get the data. If intraday, it is the first date
                data = result.json()

                print(data)
                request_num += 1
                if isinstance(data, dict):
                    # Most likely too many request error here:
                    if 'errors' in list(data.keys()):
                        print(data)
                        self.userList.checkboxes[userid].setText(f'X {userid} ERROR: Too many Requests')
                        self.userList.checkboxes[userid].setStyleSheet('color: red')
                        errorFlag = True
                        break

                    # Get the first list
                    for key in dataType.split(' '):
                        data = data[key]

                        # Handle Intraday - selection includes 'dataset'... since intraday can only grab one day
                if len(dataType.split(' ')) > 1 and dataType.split(' ')[1] == 'dataset':
                    data = []
                    intraday_dates = list(range_dates(datetime.strptime(startDate, '%Y-%m-%d').date(),
                                                      datetime.strptime(endDate, '%Y-%m-%d').date()))
                    for one_date in intraday_dates:
                        # Grab the result for the next date
                        result = UserDataRetriever.api_map[dataType](str(one_date),
                                                                     endDate)  # Since one_date is a datetime.date
                        next_day_data = result.json()

                        # Fitbit only returns the time so format it into a datetime

                        for key in dataType.split(' '):
                            next_day_data = next_day_data[key]
                        # Format time to datetime
                        next_day_data = [
                            {'datetime': datetime.strptime(f"{str(one_date)} {data['time']}", "%Y-%m-%d %H:%M:%S"),
                             'value': data['value']} for data in next_day_data]
                        # There should only be a list left
                        data += next_day_data
                        request_num += 1

                # Data is sometimes weirdly formatted with nested dictionaries. Flatten the data
                data = [flatten_dictionary(d) for d in data]
                # Format the data as a dataframe
                df = pd.DataFrame(data)
                # Make the export path
                output_path.mkdir(parents=True, exist_ok=True)
                # Export to .csv
                df.to_csv(output_path.joinpath(f'{userid}_{dataType}_{startDate}_{endDate}.csv'), index=False)

            # Turn the Userid Green Once the Export is done
            if not errorFlag:  # Because we break out of the loop
                self.userList.checkboxes[userid].setText(f'✓ {userid}')
                self.userList.checkboxes[userid].setStyleSheet('color: green')

        print(f'Time Elapsed for {request_num} requests = {time.time() - start_time}')
        # Show that the export is done
        self.doneMsgBox.setText(f'Export done! Successful exports can be found at:\n {output_path}')
        self.doneMsgBox.exec()


# class MainMenu(QWidget):
#     def __init__(self, parent):
#         super().__init__()
#         self.parent = parent
#         self.layout = QVBoxLayout()
#         self.buttonGroup = QVBoxLayout()
#         self.buttonGroupWidget = QWidget()
#         self.buttonGroupWidget.setMinimumWidth(int(int(500/2612*self.parent.scree)nsize[0]))
#         self.buttonGroupWidget.setMaximumWidth(int(800/1824*self.parent.screensize[1]))
#         # Declare the Widgets
#         self.title = QLabel("Get Fit Bit Data!")
#         self.gotoQuery = QPushButton("Query")
#         self.gotoAddDevice = QPushButton("Add Device")
#         self.testUpdateableCheckboxList = QUpdatableCheckBoxListWidget([f'Device {i}' for i in range(200)], lambda: 'Returns new item')

#         # Configure the Widgets
#         self.title.setObjectName('title')
#         self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
#         self.gotoQuery.clicked.connect(lambda: self.parent.stackedwidget.setCurrentIndex(self.parent.pageKeys['Query']))
#         self.gotoAddDevice.clicked.connect(lambda: self.parent.stackedwidget.setCurrentIndex(self.parent.pageKeys['AddDevice']))
#         self.gotoQuery.setObjectName('menubutton')
#         self.gotoAddDevice.setObjectName('menubutton')


#         # Arrange the Widgets
#         self.layout.addWidget(self.title)

#         self.buttonGroup.addWidget(self.gotoQuery)
#         self.buttonGroup.addWidget(self.gotoAddDevice)
#         self.buttonGroupWidget.setLayout(self.buttonGroup)
#         self.layout.addWidget(self.buttonGroupWidget, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

#         self.layout.addWidget(self.testUpdateableCheckboxList)
#         self.layout.addWidget(self.testbutton)

#         # Set the Layout
#         self.setLayout(self.layout)


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
    def __init__(self, get_new_item, item_names=[], add_button_label=''):
        super().__init__(item_names)
        self.clearLayoutWidgets(self.layout)
        self.menuLayout = QHBoxLayout()

        # Declare the Widgets
        self.addItemButton = QPushButton(add_button_label)

        # Configure the widgets
        self.addItemButton.clicked.connect(lambda: self.addItem(get_new_item()))

        # Arrange the Widgets
        self.menuLayout.addWidget(self.selectAllCheckbox)
        self.menuLayout.addWidget(self.addItemButton, alignment=Qt.AlignmentFlag.AlignRight)

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
            self.checkboxList.setItemWidget(listwidgetItem, self.checkboxes[item_name])
        else:
            print('Already added or Nothing Inputted')
            return


# ==================================================
# ==================================================
def run(resourcepath, db_path):
    app = QApplication(sys.argv)
    connectMsgBox = QMessageBox()
    connectMsgBox.setText('There is no internet connection. Please check your Internet Connection.')
    connectMsgBox.setIcon(QMessageBox.Icon.Critical)
    if have_internet():
        screen = app.screens()[0]
        window = MainWindow(resourcepath, db_path, screen.availableGeometry().width(),
                            screen.availableGeometry().height())
        for font_path in Path(resourcepath).joinpath('fonts').glob('*.ttf'):
            QFontDatabase.addApplicationFont(str(font_path))
        arrow_path = str(Path(resourcepath).joinpath('images', 'icons', 'cil-arrow-bottom.png')).replace('\\', '/')
        # overall_font_size = int(round(20/1824*window.screensize[1]))
        # title_font_size = overall_font_size + 4
        # fieldlabel_font_size = overall_font_size - 2
        # visualizationtitle_font_size = overall_font_size +3
        window.show()
        window.center(screen)
        stylesheet = (open(str(Path(resourcepath).joinpath('themes', 'path_theme.qss')), "r").read() % (arrow_path))
        window.setStyleSheet(stylesheet)
        window.setWindowIcon(
            QIcon(str(Path(resourcepath).joinpath('images', 'icons', 'favicon.ico')).replace('\\', '/')))
        window.setWindowTitle('PATH - Fitbit Extractor')
        app.exec()
    else:
        connectMsgBox.exec()

