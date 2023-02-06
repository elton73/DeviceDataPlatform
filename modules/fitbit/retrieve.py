import requests


class DataGetter():
    ''' Class that use the fitbit Web Api to get data, returns the entire response object'''

    def __init__(self, token):
        self.token = token
        self.api_map = {
            'weight': self.get_weight,
            'activities-steps': self.get_steps,
            'sleep': self.get_sleep,
            'devices': self.get_all_devices,
            # 'activities-heart': self.get_heartrate,
            'activities-heart-intraday dataset': self.get_intraday_heart,
            'activities-steps-intraday dataset': self.get_intraday_steps,
            'activities-elevation-intraday dataset': self.get_intraday_elevation
        }

    def get_all_devices(self, startDate, endDate):
        return requests.get('https://api.fitbit.com/1/user/-/devices.json',
                            headers={'authorization': f'Bearer {self.token}'})

    def get_weight(self, startDate, endDate):
        return requests.get(f'https://api.fitbit.com/1/user/-/body/log/weight/date/{startDate}/{endDate}.json',
                            headers={'authorization': f'Bearer {self.token}'})

    def get_sleep(self, startDate, endDate):
        return requests.get(f'https://api.fitbit.com/1.2/user/-/sleep/date/{startDate}/{endDate}.json',
                            headers={'authorization': f'Bearer {self.token}'})

    def get_steps(self, startDate, endDate):
        return requests.get(f'https://api.fitbit.com/1/user/-/activities/steps/date/{startDate}/{endDate}.json',
                            headers={'authorization': f'Bearer {self.token}'})

    def get_heartrate(self, startDate, endDate):
        return requests.get(f'https://api.fitbit.com/1/user/-/activities/heart/date/{startDate}/{endDate}.json',
                            headers={'authorization': f'Bearer {self.token}'})

    def get_intraday_heart(self, startDate, endDate):
        return requests.get(
            f'https://api.fitbit.com/1/user/-/activities/heart/date/{startDate}/{startDate}/1min/time/00:00/23:59.json',
            headers={'authorization': f'Bearer {self.token}'})

    def get_intraday_steps(self, startDate, endDate):
        return requests.get(
            f'https://api.fitbit.com/1/user/-/activities/steps/date/{startDate}/{startDate}/1min/time/00:00/23:59.json',
            headers={'authorization': f'Bearer {self.token}'})

    def get_intraday_elevation(self, startDate, endDate):
        return requests.get(
            f'https://api.fitbit.com/1/user/-/activities/elevation/date/{startDate}/{startDate}/1min/time/00:00/23:59.json',
            headers={'authorization': f'Bearer {self.token}'})
