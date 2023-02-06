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

def get_fitbit_auth_info():
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
        return False

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

# if __name__=="__main__":
    # callback_url = '127.0.0.1:8080'
    # auth_code_request_url = f'''https://www.google.com'''
    # chromedriver_autoinstaller.install(cwd=True)
    # chrome_options = webdriver.chrome.options.Options()
    # chrome_options.add_argument("log-level=3")
    # chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # driver = webdriver.Chrome(options=chrome_options)
    # driver.get(auth_code_request_url)
    # wait = ui.WebDriverWait(driver, 200)
    # wait.until(lambda driver: callback_url in driver.current_url)
    # authorization_code = driver.current_url
    # driver.quit()
