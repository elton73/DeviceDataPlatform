from modules.mysql.setup import create_engine

FITBIT_DATABASE = 'fitbit'
WITHINGS_DATABASE = 'withings'
POLAR_DATABASE = 'polar'
AUTH_DATABASE = "authorization_info"
FITBIT_ENGINE = create_engine('mysql+pymysql://newwriter:password@localhost/fitbit')
WITHINGS_ENGINE = create_engine('mysql+pymysql://newwriter:password@localhost/withings')
POLAR_ENGINE = create_engine('mysql+pymysql://newwriter:password@localhost/polar')