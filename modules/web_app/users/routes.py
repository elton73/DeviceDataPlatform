from flask import Blueprint
from flask import render_template, url_for, flash, redirect, session
from modules.web_app.users.forms import RegistrationForm, LoginForm
from modules.mysql.report import check_login_details, check_input_key
from modules.mysql.modify import add_web_app_user, link_user_to_key
from modules.web_app import bcrypt
from modules import LOGIN_DATABASE
from modules.mysql.setup import connect_to_database
from generate_key import gen_random_key

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
        with connect_to_database(LOGIN_DATABASE) as login_db:
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
        with connect_to_database(LOGIN_DATABASE) as login_db:
            if check_input_key(form.key.data, login_db): #Check if they have a key to register
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                add_web_app_user(form.email.data, hashed_password, form.username.data, login_db)
                link_user_to_key(form.key.data, form.email.data ,login_db)
                flash(f'Account created for {form.username.data}!', 'success')
                return redirect(url_for('main.home'))
            else:
                flash('Registration Unsuccessful', 'danger')  #todo: Provide details for why unsuccessful later
    return render_template('register.html', title='Register', form=form)

@users.route('/keys', methods=['GET', 'POST'])
def keys():
    # user must be logged in
    if 'logged_in' not in session:
        return redirect(url_for('users.login'))
    #display the key only if it is unused
    if not session.get('key_count'):
        session['key_count'] = 1
    key = None
    with connect_to_database(LOGIN_DATABASE) as login_db:
        if session.get('key') and check_input_key(session.get('key'), login_db):
            key = session['key']
    return render_template('keys.html', title='Keys', key=key)

@users.route('/create_keys', methods=['GET', 'POST'])
def create_key():
    # user must be logged in
    if 'logged_in' not in session:
        return redirect(url_for('users.login'))
    if session.get('key_count'):
        #set a max of 10 registration keys per session
        if session['key_count'] < 10:
            key = gen_random_key()
            session['key'] = key
            session['key_count'] += 1
        else:
            flash('Max Keys Generated. Please Try Again Later', 'danger')  # todo:Provide details for why unsuccessful later
    return redirect(url_for('users.keys'))


@users.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('users.login'))

#don't cache pages
@users.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response