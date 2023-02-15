import os
import sys
import base64
import requests

CLIENT_ID = os.environ.get('POLAR_CLIENT_ID')
CLIENT_SECRET = os.environ.get('POLAR_CLIENT_SECRET')
ACCESS_TOKEN_URL = 'https://polarremote.com/v2/oauth2/token'

SYS_DEFAULT_ENCODING = sys.getdefaultencoding()

class PolarAccess(object):
    def __init__(self):
        self.response_type = 'code'
        self.authorization_url = self.build_auth_url()
        self.access_token_url = ACCESS_TOKEN_URL
        self.challenge_code = self.generate_challenge_code()

    def build_auth_url(self):
        return f'''https://flow.polar.com/oauth2/authorization?response_type={self.response_type}&client_id={CLIENT_ID}'''

    def generate_challenge_code(self):
        code = f"""{CLIENT_ID}:{CLIENT_SECRET}""".encode(SYS_DEFAULT_ENCODING)
        return "Basic " + base64.urlsafe_b64encode(code).decode("utf-8")

    def exchange_token(self, authorization_code):
        try:
            # Exchange the code for a token
            token_exchange_url = f'https://polarremote.com/v2/oauth2/token'
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': self.challenge_code}
            payload = {
                'grant_type': 'authorization_code',
                'code': authorization_code
            }
            token_json = requests.post(token_exchange_url, headers=headers, data=payload)
            result = token_json.json()
            # Format data
            result['device_type'] = 'polar'
            result['user_id'] = result.pop('x_user_id')
            result['refresh_token'] = None
            return result
        except Exception as e:
            print(e)
        return False