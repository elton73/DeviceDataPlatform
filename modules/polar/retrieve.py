import requests
import time, datetime
from modules import POLAR_ENGINE

class DataGetter():
    ''' Class that use the withings Web Api to get data, returns the entire response object'''
    def __init__(self, token):
        self.token = token
        self.api_map = {
        }


