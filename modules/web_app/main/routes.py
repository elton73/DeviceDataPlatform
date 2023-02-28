from flask import Blueprint
from flask import render_template, url_for, flash, redirect, session, request
from modules.mysql.setup import connect_to_database
from modules.mysql.report import get_device_users, check_valid_device
from modules.mysql.modify import export_patient_data, export_device_to_auth_info
from modules.web_app import GRAFANA_URL, fitbit, withings, polar
from modules import FITBIT_DATABASE, WITHINGS_DATABASE, POLAR_DATABASE, AUTH_DATABASE

main = Blueprint('main', __name__)

@main.route('/home')
def home():
    #check if user is logged in
    if 'logged_in' in session:
        #initialize list of all the patients to be passed to html
        all_patients = []
        databases = [
            connect_to_database(FITBIT_DATABASE),
            connect_to_database(WITHINGS_DATABASE),
            connect_to_database(POLAR_DATABASE)
        ]

        # Add all patients using different devices into a list.
        all_patients = []
        # search function
        search = request.args.get('q')
        if search:
            search = search.lower()
            for db in databases:
                for user in get_device_users(db):
                    if (search in user['patient_id'].lower()) or \
                            (search in user['userid'].lower()) or \
                            (search in user['device_type'].lower()):
                        all_patients.append(user)
        else:
            all_patients = [user for db in databases for user in get_device_users(db)]

        return render_template('home.html', patients=all_patients)
    else:
        #return to login page if user is not logged in
        return redirect(url_for('users.login'))

#don't cache pages
@main.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@main.route("/oauth2_callback")
def callback():
    authorization_code = request.args.get('code')
    if session['device_type'] == "fitbit":
        auth_info = fitbit.exchange_token(authorization_code)
    elif session['device_type'] == "withings":
        auth_info = withings.exchange_token(authorization_code)
    elif session['device_type'] == "polar":
        auth_info = polar.exchange_token(authorization_code)
    #check if authentication was successful
    if not auth_info:
        flash('Authentication Failed', 'danger')
        return redirect(url_for('patients.addpatient'))

    #setup database connections
    auth_db = connect_to_database(AUTH_DATABASE)
    device_db = connect_to_database(session.get('database'))
    patient_id = session.get('patient_id')

    user_id = auth_info['user_id']
    #check if device already exists
    valid_device, message = check_valid_device(user_id, patient_id, auth_db, device_db)
    if not valid_device:
        flash(f'{message}', 'danger')
        return redirect(url_for('patients.addpatient'))

    # export data to sql database
    export_device_to_auth_info(auth_info, auth_db)
    export_patient_data(user_id, session.get('patient_id'), session.get('device_type'), device_db)
    flash('Patient Added', 'success')
    return redirect(url_for('main.home'))

@main.route("/grafana")
def data():
    return redirect(f"{GRAFANA_URL}")