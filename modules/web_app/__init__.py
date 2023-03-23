from flask import Flask
from flask_bcrypt import Bcrypt
import secrets
import os

GRAFANA_URL = os.environ.get("GRAFANA_URL")
DATAPLATFORM_URL = os.environ.get("DATAPLATFORM_URL")

from modules.polar.authorization import PolarAccess
from modules.fitbit.authorization import FitbitAccess
from modules.withings.authorization import WithingsAccess

polar = PolarAccess()
fitbit = FitbitAccess()
withings = WithingsAccess()

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
bcrypt = Bcrypt(app)

from modules.web_app.users.routes import users
from modules.web_app.patients.routes import patients
from modules.web_app.main.routes import main


app.register_blueprint(users)
app.register_blueprint(patients)
app.register_blueprint(main)