from flask import Flask
from modules.mysql.setup import connect_to_database
from flask_bcrypt import Bcrypt
from modules.polar.authorization import PolarAccess
from modules.fitbit.authorization import FitbitAccess
from modules.withings.authorization import WithingsAccess
from secret_keys import secrets
from modules import LOGIN_DATABASE

polar = PolarAccess()
fitbit = FitbitAccess()
withings = WithingsAccess()

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.get('SECRET_KEY')
login_db = connect_to_database(LOGIN_DATABASE)
login_db_cursor = login_db.cursor()
bcrypt = Bcrypt(app)
GRAFANA_URL = "https://2906-142-244-4-194.ngrok.io"


from modules.web_app.users.routes import users
from modules.web_app.patients.routes import patients
from modules.web_app.main.routes import main

app.register_blueprint(users)
app.register_blueprint(patients)
app.register_blueprint(main)