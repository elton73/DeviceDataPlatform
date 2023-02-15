'''This package will open up a browser and retrieve the Access token'''
import requests
from selenium import webdriver
import selenium.webdriver.support.ui as ui
import chromedriver_autoinstaller
import os
import sys
import re
# Hashing
import base64

SYS_DEFAULT_ENCODING = sys.getdefaultencoding()
CLIENT_ID = os.environ.get('POLAR_CLIENT_ID')
CLIENT_SECRET = os.environ.get('POLAR_CLIENT_SECRET')

def generate_challenge_code():
    code = f"""{CLIENT_ID}:{CLIENT_SECRET}""".encode(SYS_DEFAULT_ENCODING)
    return "Basic " + base64.urlsafe_b64encode(code).decode("utf-8")

def get_polar_auth_info():
    response_type = 'code'
    challenge_code = generate_challenge_code()
    callback_url = '127.0.0.1:8080'

    try:
        auth_code_request_url = f'''https://flow.polar.com/oauth2/authorization?response_type={response_type}&client_id={CLIENT_ID}'''
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
        code_p = re.compile('code=[\d\w]+')
        authorization_code = code_p.search(authorization_code)[0].replace('code=', '').replace('#', '')

        # Exchange the code for a token
        token_exchange_url = f'https://polarremote.com/v2/oauth2/token'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': challenge_code}
        payload = {
            'grant_type': 'authorization_code',
            'code': authorization_code
        }
        token_json = requests.post(token_exchange_url, headers=headers, data=payload)
        result = token_json.json()
        #Format data
        result['device_type'] = 'polar'
        result['user_id'] = result.pop('x_user_id')
        result['refresh_token'] = None
        return result
    except Exception as e:
        print(e)
        return False

def delete_polar_user(user_id, token):
    r = requests.delete(f'https://www.polaraccesslink.com/v3/users/{user_id}', headers={
        'Authorization': f'Bearer {token}'},
        )
    print(r)
    return r

if __name__=="__main__":
    user_id = '59745643'
    token = '549532da63f628c155edf2d30045297b'
    delete_polar_user(user_id, token)

