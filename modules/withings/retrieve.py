import requests
import time, datetime

class DataGetter():
    ''' Class that use the withings Web Api to get data, returns the entire response object'''
    def __init__(self, token):
        self.token = token
        self.api_map = {
            'sleep': self.get_sleep,
        }

    def str_to_unix(self, s):
        return int(time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d").timetuple()))

    def get_sleep(self, startDate, endDate):
        return requests.get(f'https://wbsapi.withings.net/v2/sleep?action=get&startdate={self.str_to_unix(startDate)}&enddate={self.str_to_unix(endDate)}&data_fields=hr,rr,snoring', headers={'Authorization': f'Bearer {self.token}'})
