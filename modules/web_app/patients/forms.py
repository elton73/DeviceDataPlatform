from modules import FITBIT_DATABASE
from modules.mysql.setup import connect_to_database
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, ValidationError
from wtforms import StringField, SubmitField, SelectField


# Check if patient_id exists in database (Deprecated)
def validate_fitbit_patient_id(FlaskForm, patient):
    # Connect to database
    fitbit_db = connect_to_database(FITBIT_DATABASE)
    cursor = fitbit_db.cursor()
    cursor.execute(f"SELECT * FROM patient_ids WHERE patient_id = '{patient.data}'")
    if cursor.fetchall():
        raise ValidationError("Patient Name Already Exists")

class PatientForm(FlaskForm):
    choices = [('fitbit', 'Fitbit'), ('withings', 'Withings'), ('polar', 'Polar')]

    patient = StringField('Patient ID',
                          validators=[DataRequired(), Length(min=2, max=20)])

    device_type = SelectField('Device Type',
                              choices=choices)
    submit = SubmitField('Submit')

class EditPatientForm(FlaskForm):
    patient = StringField('New Patient ID:',
                          validators=[DataRequired(), Length(min=2, max=20)])
    change_one = SubmitField('Change')
    change_all = SubmitField('Change All')