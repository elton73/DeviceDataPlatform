'''Script to query the Withings WebAPI'''
'''This package will open up a browser and retrieve the Access token'''
import requests
from selenium import webdriver
import selenium.webdriver.support.ui as ui
import chromedriver_autoinstaller
import sys
import re

# API Retrieiver
# retrieve data
if __name__ == "__main__":
    from retrieve import DataGetter
else:
    from .retrieve import DataGetter

SYS_DEFAULT_ENCODING = sys.getdefaultencoding()
CLIENT_ID = "d96eba460244559633e00680cddde41a26a13ebc0dc79a579cc94821479453f5"
CLIENT_SECRET = "b6d749ee51bcb761afd8b0ca02d16cdd148fd39e2e03eac05334465e85f04d25"

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

if __name__ == "__main__":
    auth_info = get_withings_auth_info()
    print(auth_info)
    datagetter = DataGetter(auth_info['access_token'])
    data = datagetter.get_sleep('2023-02-07', '2023-02-08').json()
    print(datagetter.get_sleep('2023-02-06', '2023-02-08').json())

    # print('get_auth_info:', auth_info)
    # datagetter = DataGetter(auth_info['access_token'])
    # print(datagetter.get_sleep('2023-01-01', '2023-01-24').json())
    # print('get_refreshed_auth_info:', get_refreshed_auth_info(auth_info['user_id'], auth_info['refresh_token']))
