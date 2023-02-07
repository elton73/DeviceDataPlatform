from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from modules.mysql.setup import connect_to_database
from modules import FITBIT_DATABASE


# Check if email exists in database
def validate_email(FlaskForm, email):
    # Connect to database
    database = "webapp_login_info"
    db = connect_to_database(database)
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM login_info WHERE email = '{email.data}'")
    if cursor.fetchall():
        raise ValidationError("Email Already Exists")


# Check if they have a registration key
def validate_key(FlaskForm, key):
    # Connect to database
    database = "webapp_login_info"
    db = connect_to_database(database)
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM registration_keys WHERE user_key = '{key.data}' AND email IS NULL")
    if not cursor.fetchall():
        raise ValidationError("Invalid Key")

# Check if patient_id exists in database (Deprecated)
def validate_fitbit_patient_id(FlaskForm, patient):
    # Connect to database
    fitbit_db = connect_to_database(FITBIT_DATABASE)
    cursor = fitbit_db.cursor()
    cursor.execute(f"SELECT * FROM patient_ids WHERE patient_id = '{patient.data}'")
    if cursor.fetchall():
        raise ValidationError("Patient Name Already Exists")

class RegistrationForm(FlaskForm):
    key = StringField('Key',
                      validators=[DataRequired(), Length(min=2, max=10), validate_key])
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email(), validate_email])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class PatientForm(FlaskForm):
    choices = [('fitbit', 'Fitbit'), ('withings', 'Withings'), ('polar', 'Polar')]

    patient = StringField('Patient ID',
                          validators=[DataRequired(), Length(min=2, max=20)])

    device_type = SelectField('Device Type',
                              choices=choices)

    submit = SubmitField('Submit')


if __name__ == '__main__':
    db = connect_to_database("webapp_login_info")
