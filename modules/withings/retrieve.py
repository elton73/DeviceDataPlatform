'''
Class that use the withings Web Api to get data, returns the entire response object
'''
import requests
import time, datetime

class DataGetter():
    def __init__(self, token):
        self.token = token
        self.api_map = {
            'heart_rate': self.get_heart_rate,
            'respiration_rate': self.get_respiration_rate,
            'snoring_time': self.get_snoring_time,
            'sleep_time': self.get_sleep_time,
            # 'sleep_awake_time': self.get_sleep_awake_time
        }
    def str_to_unix(self, s):
        return int(time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d").timetuple()))
    def get_heart_rate(self, startDate, endDate):
        return requests.get(f'https://wbsapi.withings.net/v2/sleep?action=get&startdate={self.str_to_unix(startDate)}&enddate={self.str_to_unix(endDate)}&data_fields=hr',
                            headers={'Authorization': f'Bearer {self.token}'})

    def get_respiration_rate(self, startDate, endDate):
        return requests.get(f'https://wbsapi.withings.net/v2/sleep?action=get&startdate={self.str_to_unix(startDate)}&enddate={self.str_to_unix(endDate)}&data_fields=rr',
                            headers={'Authorization': f'Bearer {self.token}'})

    def get_snoring_time(self, startDate, endDate):
        return requests.get(f'https://wbsapi.withings.net/v2/sleep?action=get&startdate={self.str_to_unix(startDate)}&enddate={self.str_to_unix(endDate)}&data_fields=snoring',
                            headers={'Authorization': f'Bearer {self.token}'})

    def get_sleep_time(self, startDate, endDate):
        return requests.get(f'https://wbsapi.withings.net/v2/sleep?action=getsummary&startdateymd={startDate}&enddateymd={startDate}&data_fields=total_sleep_time,waso',
                            headers={'Authorization': f'Bearer {self.token}'})

    # def get_sleep_awake_time(self, startDate, endDate):
    #     return requests.get(f'https://wbsapi.withings.net/v2/sleep?action=getsummary&startdateymd=2023-02-07&enddateymd=2023-02-08&data_fields=waso',
    #                         headers={'Authorization': f'Bearer {self.token}'})

