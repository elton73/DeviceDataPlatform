from flask import Flask, render_template

app = Flask(__name__)

posts = [
    {
        'author': 'Elton Lam',
        'title': 'Post 1',
        'content': 'First Post',
        'data_posted': 'Jan 12, 2023'
    }
]

@app.route('/')
@app.route('/home')
def home():  # put application's code here
    return render_template('home.html', posts=posts)

@app.route('/about')
def about():  # put application's code here
    return render_template('about.html', title='About')

if __name__ == '__main__':
    app.run(debug=True)
