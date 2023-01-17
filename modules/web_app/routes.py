from flask import render_template, url_for, flash, redirect, session
from modules.mysql.setup import connect_to_database
from modules.web_app.forms import RegistrationForm, LoginForm
from modules.mysql.report import check_login_details, check_input_key, get_all_device_types
from modules.mysql.modify import add_web_app_user, link_user_to_key
from modules.web_app import app, login_db, bcrypt

DEVICE_DATABASE = "authorization_info"

@app.route('/home')
def home():
    if 'logged_in' in session:
        #Get database information
        db = connect_to_database(DEVICE_DATABASE)
        all_devices = get_all_device_types(db)
        return render_template('home.html', devices=all_devices)
    else:
        return redirect(url_for('login'))

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
            try:
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                add_web_app_user(form.email.data, hashed_password, form.username.data, login_db)
                link_user_to_key(form.key.data, form.email.data ,login_db)
                flash(f'Account created for {form.username.data}!', 'success')
                return redirect(url_for('home'))
            except:
                pass
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

# if __name__ == '__main__':

