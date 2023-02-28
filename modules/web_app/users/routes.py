from flask import Blueprint
from flask import render_template, url_for, flash, redirect, session
from modules.web_app.users.forms import RegistrationForm, LoginForm
from modules.mysql.report import check_login_details, check_input_key
from modules.mysql.modify import add_web_app_user, link_user_to_key
from modules.web_app import login_db, bcrypt

users = Blueprint('users', __name__)

@users.route('/', methods=['GET', 'POST'])
@users.route('/login', methods=['GET', 'POST'])
def login():
    # if user is already logged in, redirect to home page
    if 'logged_in' in session:
        return redirect(url_for('main.home'))
    form = LoginForm()
    #validate login credentials
    if form.validate_on_submit():
        user = check_login_details(form.email.data, form.password.data, login_db)
        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            flash('Login Successful!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Invalid Username or Password', 'danger')
    return render_template('login.html', title='Login', form=form)


@users.route('/register', methods=['GET', 'POST'])
def register():
    #if user is logged in, register returns to homepage
    if "logged_in" in session:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if check_input_key(form.key.data, login_db): #Check if they have a key to register
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            add_web_app_user(form.email.data, hashed_password, form.username.data, login_db)
            link_user_to_key(form.key.data, form.email.data ,login_db)
            flash(f'Account created for {form.username.data}!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Registration Unsuccessful', 'danger')  # Provide details for why unsuccessful later
    return render_template('register.html', title='Register', form=form)

@users.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('users.login'))