import requests
import re
import time, datetime
from modules import POLAR_ENGINE

class DataGetter():
    ''' Class that use the withings Web Api to get data, returns the entire response object'''
    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id
        self.transaction_id = '265934071' #self.get_transaction_id()
        self.exercise_ids = self.get_exercise_ids()
        self.api_map = {
            'exercise_summary': self.get_exercise_summary,
            'heart_rate': self.get_heart_rate_samples
        }
    def get_exercise_summary(self):
        exercise_summary = []
        for exercise_id in self.exercise_ids:
            r = requests.get(
                f'https://www.polaraccesslink.com/v3/users/{self.user_id}/exercise-transactions/{self.transaction_id}/exercises/{exercise_id}',
                headers={
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {self.token}'}
            )
            if r.status_code >= 200 and r.status_code < 400:
                exercise_summary.append(r.json())
            else:
                print(r)
        return exercise_summary

    def get_heart_rate_samples(self):
        samples = []
        for exercise_id in self.exercise_ids:
            r = requests.get(f'https://www.polaraccesslink.com/v3/users/{self.user_id}/exercise-transactions/{self.transaction_id}/exercises/{exercise_id}/samples/1',
                headers={
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {self.token}'}
            )
            if r.status_code >= 200 and r.status_code < 400:
                data = r.json()
                #add exercise_id to data
                data['id'] = exercise_id
                samples.append(data)
            else:
                print(r)
        return samples
    def get_transaction_id(self):
        transaction_id = None
        r = requests.post(f'https://www.polaraccesslink.com/v3/users/{self.user_id}/exercise-transactions',
            headers={
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}'}
            )
        if r.status_code >= 200 and r.status_code < 400:
            try:
                transaction_id = r.json()['transaction-id']
                print(transaction_id)#debug
            except:
                print("Cannot get transaction id")
        return transaction_id

    def get_exercise_ids(self):
        exercise_ids = set()
        r = requests.get(f'https://www.polaraccesslink.com/v3/users/{self.user_id}/exercise-transactions/{self.transaction_id}',
             headers={
                 'Accept': 'application/json',
                 'Authorization': f'Bearer {self.token}'}
             )
        if r.status_code >= 200 and r.status_code < 400:
            results = r.json()['exercises']
            for result in results:
                exercise_id = re.findall('exercises/(\d+)', result)
                exercise_ids.add(exercise_id[0] if exercise_id else exercise_id)
        else:
            print(r)
        return exercise_ids

    def commit_transaction(self):
        r = requests.put(f'https://www.polaraccesslink.com/v3/users/{self.user_id}/exercise-transactions/{self.transaction_id}',
            headers={
                'Authorization': f'Bearer {self.token}'}
            )
        if not r.status_code >= 200 and not r.status_code < 400:
            print(r)
        return






