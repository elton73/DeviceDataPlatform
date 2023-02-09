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
import uuid
import hashlib

from urllib.parse import urlencode

# retrieve data
# if __name__ == "__main__":
#     from retrieve import DataGetter
# else:
#     from .retrieve import DataGetter

SYS_DEFAULT_ENCODING = sys.getdefaultencoding()
CLIENT_ID = "bb5b7afd-8a82-4bd2-a9d0-075298f069c0"
CLIENT_SECRET = "3b975aa7-3a29-44a2-8d58-4f3ad5d2a63d"

def generate_challenge_code():
    code = f"""{CLIENT_ID}:{CLIENT_SECRET}""".encode(SYS_DEFAULT_ENCODING)
    return "Basic " + base64.urlsafe_b64encode(code).decode("utf-8")

def get_polar_auth_info():
    response_type = 'code'
    challenge_code = generate_challenge_code()
    callback_url = '127.0.0.1:8080'

    # try:
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
    result['device_type'] = 'polar'
    return result
    # except Exception as e:
    #     print(e)
    #     return False

if __name__=="__main__":
    print(get_polar_auth_info())
    # token = '78e0f1fcf7472c4b344e1d206f7f0c81'
    # user_id = '59745643'
    # member_id = uuid.uuid4().hex

    # r = requests.post('https://www.polaraccesslink.com/v3/users', headers = {
    #     'Content-Type': 'application/json',
    #     'Accept': 'application/json',
    #     'Authorization': f'Bearer {token}'},
    #     json={"member-id": member_id},
    #     )
    #
    # # r = requests.delete(f'https://www.polaraccesslink.com/v3/users/{user_id}', headers = {
    # #     'Authorization': 'Bearer da821fd500ca1e1f4b68d1db16dcee52'},
    # #     json={"member-id": member_id},
    # #     )
    # print(r.json())
    # print(r)
    # print(r.json())

    # h = requests.post(f'https://www.polaraccesslink.com/v3/users/{user_id}/physical-information-transactions',headers = {
    #     'Accept': 'application/json',
    #     'Authorization': f'Bearer {token}'},
    #     )
    # print(h)
    # print(h.json())
    # tid = '18821591'
    # pid1 = '13383488'
    # pid2 = '13389385'
    # pid3 = '13389386'

    # r = requests.get(
    #     f'https://www.polaraccesslink.com/v3/users/{user_id}/physical-information-transactions/{tid}',
    #     headers={
    #         'Accept': 'application/json', 'Authorization': f'Bearer {token}'
    #     }
    #     )
    # print(r)
    # print(r.json())

    # headers = {
    #   'Accept': 'application/json',  'Authorization': f'Bearer {token}'
    # };
    #
    # r = requests.get(f'https://www.polaraccesslink.com/v3/users/{user_id}/physical-information-transactions/{tid}/physical-informations/{pid3}', headers = headers
    #     )
    # print(r)
    # print(r.json())