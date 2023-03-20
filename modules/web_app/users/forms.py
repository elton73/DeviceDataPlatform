from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from modules.mysql.setup import connect_to_database
from modules.mysql.report import email_exists, key_is_valid
from modules import LOGIN_DATABASE

# Check if email exists in database
def validate_email(FlaskForm, email):
    # Connect to database
    with connect_to_database(LOGIN_DATABASE) as db:
        if email_exists(db, email.data):
            raise ValidationError("Email Already Exists")

# Check if they have a registration key
def validate_key(FlaskForm, key):
    # Connect to database
    with connect_to_database(LOGIN_DATABASE) as db:
        if not key_is_valid(db, key.data):
            raise ValidationError("Invalid Key")

class RegistrationForm(FlaskForm):
    key = StringField('Key',
                      validators=[DataRequired(), Length(min=2, max=10), validate_key])
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email(), validate_email])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=32)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


