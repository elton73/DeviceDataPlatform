'''
Setup databases here
'''
from modules.mysql.setup import setup_databases

if __name__ == '__main__':
    setup_databases()