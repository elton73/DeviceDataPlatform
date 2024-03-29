'''
Class that use the polar Web Api to get data, returns the entire response object
'''
import requests
import re

class DataGetter():
    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id
        self.transaction_id = self.get_transaction_id()
        self.exercise_ids = self.get_exercise_ids()
        self.api_map = {
            'exercise_summary': self.get_exercise_summary,
            'heart_rate': self.get_heart_rate_samples
        }
    def get_exercise_summary(self):
        if not self.exercise_ids:
            return
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
                print(f"Exercise Summary Fail {r}")
        return exercise_summary

    def get_heart_rate_samples(self):
        if not self.exercise_ids:
            return
        samples = []
        for exercise_id in self.exercise_ids:
            r = requests.get(f'https://www.polaraccesslink.com/v3/users/{self.user_id}/exercise-transactions/{self.transaction_id}/exercises/{exercise_id}/samples/0',
                headers={
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {self.token}'}
            )
            #sometimes request fails with type 0, so try type 1
            if r.status_code == 204:
                r = requests.get(
                    f'https://www.polaraccesslink.com/v3/users/{self.user_id}/exercise-transactions/{self.transaction_id}/exercises/{exercise_id}/samples/1',
                    headers={
                        'Accept': 'application/json',
                        'Authorization': f'Bearer {self.token}'}
                    )
            if r.status_code >= 200 and r.status_code < 400 and r.status_code != 204:
                data = r.json()
                #add exercise_id to data
                data['id'] = exercise_id
                samples.append(data)
            else:
                print(f"Exercise ID: {exercise_id} has no samples")
        return samples
    def get_transaction_id(self):
        transaction_id = None
        r = requests.post(f'https://www.polaraccesslink.com/v3/users/{self.user_id}/exercise-transactions',
            headers={
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}'}
            )
        if r.status_code == 204:
            print(f"User {self.user_id} has no new data. Transaction ID: {transaction_id}. Status code: {r.status_code}")
            return None
        elif r.status_code >= 200 and r.status_code < 400:
            try:
                transaction_id = r.json()['transaction-id']
            except:
                print(f"Could not get transaction id: {r}")
        else:
            print(f"Could not get transaction id: {r}")
        print(f"Transaction ID: {transaction_id}")
        return transaction_id

    def get_exercise_ids(self):
        #if no transaction
        if not self.transaction_id:
            return
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
        elif r.status_code == 404:
            print(f"No Exercises Available: {r}")
        else:
            print(f"Exercise IDs Failed: {r}")
        return exercise_ids

    def commit_transaction(self):
        r = requests.put(f'https://www.polaraccesslink.com/v3/users/{self.user_id}/exercise-transactions/{self.transaction_id}',
            headers={
                'Authorization': f'Bearer {self.token}'}
            )
        if not r.status_code >= 200 and not r.status_code < 400:
            print(r)
        return






