from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length
from wtforms import StringField, SubmitField, SelectField


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