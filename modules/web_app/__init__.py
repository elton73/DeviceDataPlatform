from flask import Flask
from modules.mysql.setup import connect_to_database, create_engine
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = '043507edf24db0e96afe4314430441bf' #A random secret key
LOGIN_DATABASE_NAME = 'webapp_login_info'
login_db = connect_to_database(LOGIN_DATABASE_NAME)
login_db_cursor = login_db.cursor()
bcrypt = Bcrypt(app)
FITBIT_DATABASE = 'test6'
AUTH_DATABASE = "authorization_info"
ENGINE = create_engine('mysql+pymysql://newwriter:password@localhost/test6')
GRAFANA_PLATFORM = "https://c5ab-142-244-4-196.ngrok.io"

from modules.web_app import routes