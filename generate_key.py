from modules.mysql.setup import create_key
import secrets
from time import sleep
import random
import string

if __name__ == "__main__":
    key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
    create_key(key) 
    print(f"Key: {key}")
    print("Please save the above key. This screen will disappear in 30 seconds.")
    sleep(30)
