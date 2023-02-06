import requests
from selenium import webdriver
import selenium.webdriver.support.ui as ui
import chromedriver_autoinstaller
import sys
import re

# API Retrieiver
# retrieve data
# if __name__ == "__main__":
#     from retrieve import DataGetter
# else:
#     from .retrieve import DataGetter

SYS_DEFAULT_ENCODING = sys.getdefaultencoding()
CLIENT_ID = "bb5b7afd-8a82-4bd2-a9d0-075298f069c0"
CLIENT_SECRET = "3b975aa7-3a29-44a2-8d58-4f3ad5d2a63d"

def get_polar_auth_info():
    response_type = 'code'
    callback_url = 'http://127.0.0.1:8080'
    try:
        auth_code_request_url =