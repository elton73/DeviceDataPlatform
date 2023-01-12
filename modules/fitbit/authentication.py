'''This package will open up a browser and retrieve the Access token'''
import requests
from selenium import webdriver
import selenium.webdriver.support.ui as ui
import chromedriver_autoinstaller



import numpy as np
import sys
import re

# Hashing
import base64
import hashlib

# retrieve data
if __name__ == "__main__":
    from retrieve import DataGetter
else:
    from .retrieve import DataGetter

SYS_DEFAULT_ENCODING = sys.getdefaultencoding()
CLIENT_ID = "23BHY7"

def generate_challenge_code(verifier=''):
    if verifier == '':
        for i in range(np.random.randint(43,129)):
            code_element = np.random.randint(0,10)
            verifier += str(code_element)
    verifier = verifier.encode(SYS_DEFAULT_ENCODING)

    challenge_code = base64.urlsafe_b64encode(hashlib.sha256(verifier).digest())

    return verifier.decode(SYS_DEFAULT_ENCODING), challenge_code.decode(SYS_DEFAULT_ENCODING).replace('=', '')

def get_auth_info():
    response_type = 'code'
    verifier, challenge_code = generate_challenge_code()
    challenge_method = 'S256'
    callback_url = '127.0.0.1:8080'

    try: 
        auth_code_request_url = f'''https://www.fitbit.com/oauth2/authorize?client_id={CLIENT_ID}&response_type={response_type}
&code_challenge={challenge_code}&code_challenge_method={challenge_method}
&scope=weight%20settings%20nutrition%20activity%20sleep
%20heartrate'''
        chromedriver_autoinstaller.install(cwd=True)
        chrome_options = webdriver.chrome.options.Options()
        chrome_options.add_argument("log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(auth_code_request_url)
        wait = ui.WebDriverWait(driver, 200)
        wait.until(lambda driver: callback_url in driver.current_url)
        authorization_code = driver.current_url
        driver.quit()

        # Clean up the returned code
        code_p = re.compile('code=[\d\w]+#')
        authorization_code = code_p.search(authorization_code)[0].replace('code=','').replace('#', '')

        # Exchange the code for a token
        token_exchange_url = f'https://api.fitbit.com/oauth2/token'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'code': authorization_code,
            'client_id': CLIENT_ID,
            'code_verifier': verifier,
            'grant_type': 'authorization_code',
            'expires_in': '10',
        }
        token_json = requests.post(token_exchange_url, headers=headers, data=payload)
        return token_json.json()
    except Exception as e:
        print(e)
        return ''
    

def get_refreshed_auth_info(userid, refresh_token):
    '''Returns same format as the first authentication'''

    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    token_exchange_url = f'https://api.fitbit.com/oauth2/token'
    result = requests.post(token_exchange_url, headers=headers, data=payload)
    if result.status_code == 400:
        # Handling of bad refresh token
        print(f'Bad refresh token, enter credentials for userid: {userid}')
        return 400
    else:
        return result.json()

if __name__=="__main__":
    # Testing if we can get the data successfully
    # auth_token = get_auth_info()['access_token']
    # DataGet = DataGetter(auth_token)
    # print(DataGet.get_all_devices())
    # print("="*50)
    # print(DataGet.get_weight(date='2021-11-16'))
    auth_token = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyM0JINTgiLCJzdWIiOiI5TlE5U0QiLCJpc3MiOiJGaXRiaXQiLCJ0eXAiOiJhY2Nlc3NfdG9rZW4iLCJzY29wZXMiOiJyc29jIHJzZXQgcmFjdCBybG9jIHJ3ZWkgcmhyIHJwcm8gcm51dCByc2xlIiwiZXhwIjoxNjM3MjEyMzU3LCJpYXQiOjE2MzcxODM1NTd9.9yikywwLz5_mOOA-_tiY6RijnybUSqL7y6BFhYPojGc'
    refresh_token = '8b2bddd17b5a79109cda8855801de6bd0fb51dc37d1bd2593d8263e31e8102c2'

    DataGet = DataGetter(auth_token)
    print(DataGet.get_all_devices())
    print("="*50)
    print(DataGet.get_weight(date='2021-11-16'))
    print(get_refreshed_auth_info(refresh_token))
