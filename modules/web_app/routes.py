from flask import render_template, url_for, flash, redirect, session
from modules.mysql.setup import connect_to_database
from modules.web_app.forms import RegistrationForm, LoginForm, PatientForm
from modules.mysql.report import check_login_details, check_input_key, get_fitbit_users, \
    check_auth_info_and_input_device
from modules.mysql.modify import add_web_app_user, link_user_to_key, export_patient_data, remove_fitbit_patient
from modules.web_app import app, login_db, bcrypt
from modules.fitbit.authentication import export_fitbit_to_auth_info

DEVICE_DATABASE = "authorization_info"
PATIENT_LABEL_DATABASE = "patient_labels"
DEVICE_TYPE_COLUMN = "device_type"
FITBIT_DATABASE = 'fitbit'

@app.route('/home')
def home():
    #check if user is logged in
    if 'logged_in' in session:
        #initialize list of all the patients to be passed to html
        all_patients = []
        #Get fitbit users
        fitbit_db = connect_to_database(FITBIT_DATABASE)
        fitbit_patients = get_fitbit_users(fitbit_db)

        #TODO:create a function for below loop
        #Add all patients using different devices into a list
        for patient in fitbit_patients:
            all_patients.append(patient)

        return render_template('home.html', patients=all_patients)
    else:
        #return to login page if user is not logged in
        return redirect(url_for('login'))

@app.route('/addpatient', methods=['GET', 'POST'])
def addpatient():
    #user must be logged in
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    #Add check for unique patient_labels and device_data later
    form = PatientForm()
    if form.validate_on_submit():
        device_type = form.device_type.data
        # check if auth_info is valid and if input device already exists. Return userid, auth_info, and success.
        auth_info, success = check_auth_info_and_input_device(device_type)
        if success:
            #export userid, patient and device type to fitbit database
            user_id = auth_info['user_id']
            patient_id = form.patient.data
            # export data to sql database
            auth_db = connect_to_database(DEVICE_DATABASE)
            export_fitbit_to_auth_info(device_type, auth_info, auth_db)
            fitbit_db = connect_to_database(FITBIT_DATABASE)
            export_patient_data(user_id, patient_id, device_type, fitbit_db)
            return redirect(url_for('home'))
        else:
            flash(f'{auth_info}', 'danger')
    return render_template('addpatient.html', title='Add', form=form)

@app.route('/patient/<string:patient_id>/<string:user_id>/delete', methods = ['POST'])
def deletepatient(patient_id, user_id):
    # user must be logged in
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    fitbit_db = connect_to_database(FITBIT_DATABASE)
    auth_db = connect_to_database(DEVICE_DATABASE)
    remove_fitbit_patient(patient_id, user_id, fitbit_db, auth_db)
    flash('Patient deleted', 'success')
    return redirect(url_for('home'))



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

