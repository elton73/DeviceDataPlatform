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
    if 'logged_in' not in session:
        return redirect(url_for('users.login'))
    databases = [FITBIT_DATABASE, WITHINGS_DATABASE, POLAR_DATABASE]
    # Add all patients using different devices into a list.
    all_patients = []
    # search function
    search = request.args.get('q')
    for db_name in databases:
        with connect_to_database(db_name) as db:
            if search:
                search = search.lower()
                for user in get_device_users(db):
                    if (search in user['patient_id'].lower()) or \
                            (search in user['userid'].lower()) or \
                            (search in user['device_type'].lower()):
                        all_patients.append(user)
            else:
                for user in get_device_users(db):
                    all_patients.append(user)

    return render_template('home.html', patients=all_patients)

#don't cache pages
@main.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@main.route("/oauth2_callback")
def callback():
    if 'logged_in' not in session:
        return redirect(url_for('users.login'))
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
    patient_id = session.get('patient_id')

    user_id = auth_info['user_id']
    #check if device already exists
    with connect_to_database(AUTH_DATABASE) as auth_db, connect_to_database(session.get('database')) as device_db:
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