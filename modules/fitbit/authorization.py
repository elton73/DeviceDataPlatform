"""
Class to generate an authorization url and get a user's access token
"""

import os
import sys
import base64
import requests
import numpy as np
import hashlib

CLIENT_ID = os.environ.get('FITBIT_CLIENT_ID')
CLIENT_SECRET = os.environ.get('FITBIT_CLIENT_SECRET')
ACCESS_TOKEN_URL = 'https://polarremote.com/v2/oauth2/token'

SYS_DEFAULT_ENCODING = sys.getdefaultencoding()

class FitbitAccess(object):
    def __init__(self):
        self.response_type = 'code'
        self.challenge_method = 'S256'
        self.verifier, self.challenge_code = self.generate_challenge_code()
        self.base64 = self.generate_base64()
        self.authorization_url = self.build_auth_url()
        self.access_token_url = ACCESS_TOKEN_URL


    def build_auth_url(self):
        return f'''https://www.fitbit.com/oauth2/authorize?client_id={CLIENT_ID}&response_type={self.response_type}&code_challenge={self.challenge_code}&code_challenge_method={self.challenge_method}&scope=weight%20settings%20nutrition%20activity%20sleep%20heartrate'''

    def generate_challenge_code(self, verifier=''):
        if verifier == '':
            for i in range(np.random.randint(43, 129)):
                code_element = np.random.randint(0, 10)
                verifier += str(code_element)
        verifier = verifier.encode(SYS_DEFAULT_ENCODING)
        challenge_code = base64.urlsafe_b64encode(hashlib.sha256(verifier).digest())
        return verifier.decode(SYS_DEFAULT_ENCODING), challenge_code.decode(SYS_DEFAULT_ENCODING).replace('=', '')

    def generate_base64(self):
        code = f"""{CLIENT_ID}:{CLIENT_SECRET}""".encode(SYS_DEFAULT_ENCODING)
        return "Basic " + base64.urlsafe_b64encode(code).decode("utf-8")

    def exchange_token(self, authorization_code):
        try:
            # Exchange the code for a token
            token_exchange_url = f'https://api.fitbit.com/oauth2/token'
            headers = {'Content-Type': 'application/x-www-form-urlencoded',
                       'Authorization': self.base64}
            payload = {
                'code': authorization_code,
                'client_id': CLIENT_ID,
                'code_verifier': self.verifier,
                'grant_type': 'authorization_code',
                'expires_in': '10',
            }
            token_json = requests.post(token_exchange_url, headers=headers, data=payload)
            result = token_json.json()
            result['device_type'] = 'fitbit'
            return result
        except Exception as e:
            print(e)
        return False
