from flask import render_template, url_for, flash, redirect, session, request
from modules.mysql.setup import connect_to_database
from modules.web_app.forms import RegistrationForm, LoginForm, PatientForm, EditPatientForm
from modules.mysql.report import check_login_details, check_input_key, get_device_users, \
    check_valid_device, get_data, check_patient_id
from modules.mysql.modify import add_web_app_user, link_user_to_key, export_patient_data, remove_patient, \
    export_device_to_auth_info, update_patientid
from modules.web_app import app, login_db, bcrypt, GRAFANA_URL
from modules import FITBIT_DATABASE, WITHINGS_DATABASE, POLAR_DATABASE, AUTH_DATABASE
from scheduled import runschedule
from modules.polar.authorization import PolarAccess
from modules.fitbit.authorization import FitbitAccess
from modules.withings.authorization import WithingsAccess

polar = PolarAccess()
fitbit = FitbitAccess()
withings = WithingsAccess()

@app.route('/home')
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
        return redirect(url_for('login'))

@app.route('/addpatient', methods=['GET', 'POST'])
def addpatient():
    #user must be logged in
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    form = PatientForm()

    #Validate user input
    if form.validate_on_submit():
        device_type = form.device_type.data
        patient_id = form.patient.data

        # save data for other routes
        session['device_type'] = device_type
        session['patient_id'] = patient_id

        if device_type == "fitbit":
            session['database'] = FITBIT_DATABASE
            return redirect(fitbit.authorization_url)
        elif device_type == "withings":
            session['database'] = WITHINGS_DATABASE
            return redirect(withings.authorization_url)
        elif device_type == "polar":
            session['database'] = POLAR_DATABASE
            return redirect(polar.authorization_url)
    return render_template('addpatient.html', title='Add', form=form)

@app.route('/patient/<string:patient_id>/<string:user_id>/delete', methods = ['POST'])
#todo: delete only the device, not all the devices with patient_id
def deletepatient(patient_id, user_id):
    # user must be logged in
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    auth_db = connect_to_database(AUTH_DATABASE)
    device_type = get_data(auth_db, user_id, 'device_type')
    #todo: use select_database function
    if device_type == 'fitbit':
        device_db = connect_to_database(FITBIT_DATABASE)
    elif device_type == 'withings':
        device_db = connect_to_database( WITHINGS_DATABASE)
    elif device_type == 'polar':
        device_db = connect_to_database(POLAR_DATABASE)
    remove_patient(patient_id, user_id,device_type, device_db, auth_db)
    flash('Patient Deleted', 'success')
    return redirect(url_for('home'))

@app.route('/patient/<string:patient_id>/<string:user_id>/<string:device_type>', methods = ['GET', 'POST'])
def editpatient(patient_id, user_id, device_type):
    # user must be logged in
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    form = EditPatientForm()
    patient_id = patient_id.replace("_", " ")
    if form.validate_on_submit():
        # update only the current patient_id. Check if new id is already in use.
        if form.change_all.data:
            device_type = "all"
        else:
            device_type = device_type
        success, message = check_patient_id(form.patient.data, device_type)
        if success:
            update_patientid(device_type, patient_id, form.patient.data)
            flash("Patient ID updated to 'form.patient.data'", 'success')
            return redirect(url_for('home'))
        else:
            flash(message, 'danger')

    return render_template('editpatient.html', title='Edit', form=form,
                           patient_id=patient_id.replace(" ", "_"), user_id=user_id, device_type=device_type)

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    # if user is already logged in, redirect to home page
    if 'logged_in' in session:
        return redirect(url_for('home'))
    form = LoginForm()
    #validate login credentials
    if form.validate_on_submit():
        user = check_login_details(form.email.data, form.password.data, login_db)
        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            flash('Login Successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Invalid Username or Password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    #if user is logged in, register returns to homepage
    if "logged_in" in session:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if check_input_key(form.key.data, login_db): #Check if they have a key to register
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            add_web_app_user(form.email.data, hashed_password, form.username.data, login_db)
            link_user_to_key(form.key.data, form.email.data ,login_db)
            flash(f'Account created for {form.username.data}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Registration Unsuccessful', 'danger')  # Provide details for why unsuccessful later
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

#don't cache pages
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@app.route('/updatenow')
def updatenow():
    request_num = runschedule()
    flash(f'Users Updated: {request_num}', 'info')
    return redirect(url_for('home'))

@app.route("/oauth2_callback")
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
        return redirect(url_for('addpatient'))

    #setup database connections
    auth_db = connect_to_database(AUTH_DATABASE)
    device_db = connect_to_database(session.get('database'))
    patient_id = session.get('patient_id')

    user_id = auth_info['user_id']
    #check if device already exists
    valid_device, message = check_valid_device(user_id, patient_id, auth_db, device_db)
    if not valid_device:
        flash(f'{message}', 'danger')
        return redirect(url_for('addpatient'))

    # export data to sql database
    export_device_to_auth_info(auth_info, auth_db)
    export_patient_data(user_id, session.get('patient_id'), session.get('device_type'), device_db)
    flash('Patient Added', 'success')
    return redirect(url_for('home'))

@app.route("/grafana")
def data():
    return redirect(f"{GRAFANA_URL}")

