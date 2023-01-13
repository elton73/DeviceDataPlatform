from flask import Flask, render_template, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from forms import RegistrationForm, LoginForm
from modules.mysql.setup import connect_to_database
from modules.mysql.modify import check_login_details
app = Flask(__name__)

app.config['SECRET_KEY'] = '043507edf24db0e96afe4314430441bf'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'


DATABASE_NAME = 'webapp_login_info'
db = connect_to_database(DATABASE_NAME)
cursor = db.cursor()

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
        if check_login_details(form.email.data, form.password.data, cursor):
            flash('Login Successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Invalid Username or Password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home'))

    return render_template('register.html', title='Register', form=form)

if __name__ == '__main__':
    app.run(debug=True)



