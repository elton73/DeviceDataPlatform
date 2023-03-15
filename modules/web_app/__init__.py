from flask import Flask
from flask_bcrypt import Bcrypt
from secret_keys import secrets

GRAFANA_URL = "https://6cf8-142-244-4-196.ngrok.io"
DATAPLATFORM_URL = "https://953c-142-244-4-196.ngrok.io"

from modules.polar.authorization import PolarAccess
from modules.fitbit.authorization import FitbitAccess
from modules.withings.authorization import WithingsAccess

polar = PolarAccess()
fitbit = FitbitAccess()
withings = WithingsAccess()

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.get('SECRET_KEY')
bcrypt = Bcrypt(app)

from modules.web_app.users.routes import users
from modules.web_app.patients.routes import patients
from modules.web_app.main.routes import main


app.register_blueprint(users)
app.register_blueprint(patients)
app.register_blueprint(main)