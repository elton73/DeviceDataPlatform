from flask import render_template, url_for, flash, redirect
from modules.web_app.forms import RegistrationForm, LoginForm
from modules.mysql.report import check_login_details, check_input_key
from modules.mysql.modify import add_web_app_user, link_user_to_key
from modules.web_app import app, login_db, bcrypt

posts = [
    {
        'author': 'Elton Lam',
        'title': 'Post 1',
        'content': 'First Post',
        'date_posted': 'Jan 12, 2023'
    }
]

@app.route('/')
@app.route('/home')
def home():  # put application's code here
    return render_template('home.html', posts=posts)

@app.route('/about')
def about():  # put application's code here
    return render_template('about.html', title='About')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if check_login_details(form.email.data, form.password.data, login_db):
            flash('Login Successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Invalid Username or Password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if check_input_key(form.key.data, login_db): #Check if they have a key to register
            # try:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            add_web_app_user(form.email.data, hashed_password, form.username.data, login_db)
            link_user_to_key(form.key.data, form.email.data ,login_db)
            flash(f'Account created for {form.username.data}!', 'success')
            return redirect(url_for('home'))
            # except:
            #     pass
        else:
            flash('Registration Unsuccessful', 'danger')  # Provide details for why unsuccessful later
    return render_template('register.html', title='Register', form=form)