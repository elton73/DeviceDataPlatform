import os
import sys
import requests
from modules.web_app import DATAPLATFORM_URL

CLIENT_ID = os.environ.get('WITHINGS_CLIENT_ID')
CLIENT_SECRET = os.environ.get('WITHINGS_CLIENT_SECRET')
ACCESS_TOKEN_URL = 'https://wbsapi.withings.net/v2/oauth2'
CALLBACK_URL = f"{DATAPLATFORM_URL}/oauth2_callback" #todo: change this to ngrok site

SYS_DEFAULT_ENCODING = sys.getdefaultencoding()

class WithingsAccess(object):
    def __init__(self):
        self.response_type = 'code'
        self.authorization_url = self.build_auth_url()
        self.access_token_url = ACCESS_TOKEN_URL

    def build_auth_url(self):
        return f'''https://account.withings.com/oauth2_user/authorize2?response_type=code&client_id={CLIENT_ID}&state=12345&scope=user.activity&redirect_uri={CALLBACK_URL}'''

    def exchange_token(self, authorization_code):
        try:
            # Exchange the code for a token
            self.access_exchange_url = f'https://wbsapi.withings.net/v2/oauth2'
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            payload = {
                'action': 'requesttoken',
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'code': authorization_code,
                'grant_type': 'authorization_code',
                'redirect_uri': CALLBACK_URL
            }
            token_json = requests.post(self.access_exchange_url, headers=headers, data=payload)
            result = token_json.json()['body']
            # rename key to match fitbit format
            if 'userid' in result:
                result['user_id'] = result.pop('userid')
                result['device_type'] = 'withings'
            return result
        except Exception as e:
            print(e)
            return False