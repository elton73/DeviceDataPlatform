from flask import Blueprint
from flask import render_template, url_for, flash, redirect, session
from modules.mysql.setup import connect_to_database, select_database
from modules.web_app.patients.forms import PatientForm, EditPatientForm
from modules.mysql.report import get_data, check_patient_id
from modules.mysql.modify import remove_patient, update_patientid
from modules import FITBIT_DATABASE, WITHINGS_DATABASE, POLAR_DATABASE, AUTH_DATABASE
from modules.web_app import fitbit, withings, polar
from scheduled import runschedule

patients = Blueprint('patients', __name__)

@patients.route('/updatenow')
def updatenow():
    if 'logged_in' not in session:
        return redirect(url_for('users.login'))
    request_num = runschedule()
    if request_num == 0:
        flash(f'All Users Are Up To Date', 'info')
    else:
        flash(f'Users Updated: {request_num}', 'info')
    return redirect(url_for('main.home'))

@patients.route('/patient/<string:patient_id>/<string:user_id>/delete', methods = ['POST'])
#todo:check if function deletes only the device, not all the devices with patient_id
def deletepatient(patient_id, user_id):
    # user must be logged in
    if 'logged_in' not in session:
        return redirect(url_for('users.login'))
    with connect_to_database(AUTH_DATABASE) as auth_db:
        device_type = get_data(auth_db, user_id, 'device_type')
        db_name = select_database(device_type)
        with connect_to_database(db_name) as device_db:
            remove_patient(patient_id, user_id, device_type, device_db, auth_db)
    flash('Patient Deleted', 'success')
    return redirect(url_for('main.home'))

@patients.route('/patient/<string:patient_id>/<string:user_id>/<string:device_type>', methods = ['GET', 'POST'])
def editpatient(patient_id, user_id, device_type):
    # user must be logged in
    if 'logged_in' not in session:
        return redirect(url_for('users.login'))
    form = EditPatientForm()
    patient_id = patient_id.replace("_", " ")
    if form.validate_on_submit():
        # update only the current patient_id. Check if new id is already in use.
        #change all
        if form.change_all.data:
            db_names = select_database("all")
            dbs = []
            for db_name in db_names:
                dbs.append(connect_to_database(db_name))
            success, message = check_patient_id(form.patient.data, dbs)
            if success:
                update_patientid(patient_id, form.patient.data, dbs)
                flash(f"Patient ID '{patient_id}' changed to '{form.patient.data}'", 'success')
                for db in dbs:
                    db.close()
                return redirect(url_for('main.home'))
            else:
                flash(message, 'danger')
        #change one
        else:
            with connect_to_database(select_database(device_type)) as device_db:
                success, message = check_patient_id(form.patient.data, device_db)
                if success:
                    update_patientid(patient_id, form.patient.data, device_db)
                    flash(f"Patient ID '{patient_id}' changed to '{form.patient.data}'", 'success')
                    return redirect(url_for('main.home'))
                else:
                    flash(message, 'danger')
    return render_template('editpatient.html', title='Edit', form=form,
                           patient_id=patient_id.replace(" ", "_"), user_id=user_id, device_type=device_type)

@patients.route('/addpatient', methods=['GET', 'POST'])
def addpatient():
    #user must be logged in
    if 'logged_in' not in session:
        return redirect(url_for('users.login'))
    form = PatientForm()

    #Validate user input
    if form.validate_on_submit():
        device_type = form.device_type.data
        patient_id = form.patient.data

        # save data for other routes
        session['device_type'] = device_type
        session['patient_id'] = patient_id

        #todo: check for open redirect vulnerability
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

#don't cache pages
@patients.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response