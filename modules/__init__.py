from modules.mysql.setup import create_engine

DEVICE_DATABASE = 'test6'
AUTH_DATABASE = "authorization_info"
ENGINE = create_engine('mysql+pymysql://newwriter:password@localhost/test6')