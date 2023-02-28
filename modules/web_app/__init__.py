from flask import Flask
from modules.mysql.setup import connect_to_database
from flask_bcrypt import Bcrypt
from modules.polar.authorization import PolarAccess
from modules.fitbit.authorization import FitbitAccess
from modules.withings.authorization import WithingsAccess
from secret_keys import secrets

polar = PolarAccess()
fitbit = FitbitAccess()
withings = WithingsAccess()

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.get('SECRET_KEY')
LOGIN_DATABASE_NAME = 'webapp_login_info'
login_db = connect_to_database(LOGIN_DATABASE_NAME)
login_db_cursor = login_db.cursor()
bcrypt = Bcrypt(app)
GRAFANA_URL = "https://c5ab-142-244-4-196.ngrok.io"


from modules.web_app.users.routes import users
from modules.web_app.patients.routes import patients
from modules.web_app.main.routes import main

app.register_blueprint(users)
app.register_blueprint(patients)
app.register_blueprint(main)