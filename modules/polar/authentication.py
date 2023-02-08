'''This package will open up a browser and retrieve the Access token'''
import sys
from urllib.parse import urlencode

# retrieve data
# if __name__ == "__main__":
#     from retrieve import DataGetter
# else:
#     from .retrieve import DataGetter

SYS_DEFAULT_ENCODING = sys.getdefaultencoding()
CLIENT_ID = "bb5b7afd-8a82-4bd2-a9d0-075298f069c0"
CLIENT_SECRET = "3b975aa7-3a29-44a2-8d58-4f3ad5d2a63d"

AUTHORIZATION_URL = "https://flow.polar.com/oauth2/authorization"
ACCESS_TOKEN_URL = "https://polarremote.com/v2/oauth2/token"
ACCESSLINK_URL = "https://www.polaraccesslink.com/v3"

# class AccessLink(object):
#     def __init__(self, redirect_url=None):

class OAuth2Client(object):
    def __init__(self, redirect_url):
        self.accesslink_url = ACCESSLINK_URL
        self.authorziation_url = AUTHORIZATION_URL
        self.access_token_url = ACCESS_TOKEN_URL
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.redirect_url = redirect_url

    def get_auth_headers(self, access_token):
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_authorization_url(self, response_type="code"):
        params = {
            "client_id": self.client_id,
            "response_type": response_type,
        }

        if self.redirect_url:
            params["redirect_uri"] = self.redirect_url

        return "{url}?{params}".format(url=self.authorization_url,
                                       params=urlencode(params))

    def get_access_token(self, authorization_code):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json;charset=UTF-8"
        }
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code
        }
        return self.post(endpoint=None,
                         url=self.access_token_url,
                         data=data,
                         headers=headers)