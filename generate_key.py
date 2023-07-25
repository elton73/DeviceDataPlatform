"""
Generate a Registration Key
"""

from modules.mysql.setup import create_key, connect_to_database
from time import sleep
import random
import string
from modules import LOGIN_DATABASE

def gen_random_key():
    random_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
    is_unique = False
    with connect_to_database(LOGIN_DATABASE) as db:
        cursor = db.cursor()
        while not is_unique:
            cursor.execute(f"SELECT * FROM registration_keys WHERE user_key = '{random_key}'")
            if cursor.fetchone():
                random_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
            else:
                is_unique = True
                create_key(random_key)
    return random_key



if __name__ == "__main__":
    key = gen_random_key()
    print(f"Key: {key}")
    print("Please save the above key. This screen will terminate in 30 seconds.")
    sleep(30)
