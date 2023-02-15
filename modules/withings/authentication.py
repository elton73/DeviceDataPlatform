'''Script to query the Withings WebAPI'''
'''This package will open up a browser and retrieve the Access token'''
import requests
from selenium import webdriver
import selenium.webdriver.support.ui as ui
import chromedriver_autoinstaller
import sys
import re
import os

# API Retrieiver
# retrieve data
if __name__ == "__main__":
    from retrieve import DataGetter
else:
    from .retrieve import DataGetter

SYS_DEFAULT_ENCODING = sys.getdefaultencoding()
#Store API keys as environment variables
CLIENT_ID = os.environ.get('WITHINGS_CLIENT_ID')
CLIENT_SECRET = os.environ.get('WITHINGS_CLIENT_SECRET')

def get_withings_auth_info():
    response_type = 'code'
    callback_url = 'http://127.0.0.1:8080'

    try: 
        login_url = f'''https://account.withings.com/new_workflow/'''
        auth_code_request_url = f'''https://account.withings.com/oauth2_user/authorize2''' \
                            + '''?response_type=code'''\
                            + f"&client_id={CLIENT_ID}" \
                            + f"&state=12345" \
                            + f"&scope=user.activity" \
                            + f"&redirect_uri={callback_url}"
        chromedriver_autoinstaller.install(cwd=True)
        chrome_options = webdriver.chrome.options.Options()
        chrome_options.add_argument("log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(login_url)
        wait = ui.WebDriverWait(driver, 200)
        wait.until(lambda driver: 'exit' in driver.current_url)
        driver.get(auth_code_request_url)
        wait = ui.WebDriverWait(driver, 200)
        wait.until(lambda driver: callback_url in driver.current_url)
        authorization_code = driver.current_url
        driver.quit()

        # Clean up the returned code
        code_p = re.compile('code=[\d\w]+')
        authorization_code = code_p.search(authorization_code)[0].replace('code=','').replace('#', '')

        # Exchange the code for a token
        token_exchange_url = f'https://wbsapi.withings.net/v2/oauth2'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'action': 'requesttoken',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': authorization_code,
            'grant_type': 'authorization_code',
            'redirect_uri': callback_url
        }
        token_json = requests.post(token_exchange_url, headers=headers, data=payload)

        result = token_json.json()['body']
        # rename key to match fitbit format
        if 'userid' in result:
            result['user_id'] = result.pop('userid')
            result['device_type'] = 'withings'
        return result
    except Exception as e:
        print(e)
        return False


def get_refreshed_withings_auth_info(userid, refresh_token):
    '''Returns same format as the first authentication'''

    payload = {
        'action': 'requesttoken',
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    token_exchange_url = f'https://wbsapi.withings.net/v2/oauth2'
    result = requests.post(token_exchange_url, headers=headers, data=payload)
    if result.status_code == 400:
        # Handling of bad refresh token
        print(f'Bad refresh token, enter credentials for userid: {userid}')
        return 400
    else:
        return result.json()

# if __name__ == "__main__":
#     print()
