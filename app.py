from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_sqlalchemy import SQLAlchemy
# from data import Articles
from functools import wraps
from datetime import datetime

# from flask.ext.login import LoginManager

# from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, form
from  passlib.hash import sha256_crypt

app = Flask(__name__)
# login_manager = LoginManager()
# login_manager.init_app(app)


# Articles = Articles()

ENV = 'prod'
# development
if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:quickerpay@localhost/flaskcrud_db"
else:
    # production
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = "DATABASE_URL"
    # app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://qmyqkeeonlrzov:0e0fc6095953361d9a66ba03caa26a36e5b3eed71f7ef99d2ed70e6ee032757c@ec2-174-129-227-80.compute-1.amazonaws.com:5432/drccdheka65tb"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# database object
db = SQLAlchemy(app)

# Database model
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    # authenticated = db.Column(db.Boolean, default=False)
    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

# Table Constructor
def __init__(self, name, email, username, password):
    self.name = name
    self.email = email
    self.username = username
    self.password = password

class Articles(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    author = db.Column(db.String(100))
    body = db.Column(db.Text)
    date_created = db.Column(db.TIMESTAMP)


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
   return render_template('about.html')

#get all articles
@app.route('/articles')
def articles():
    article = Articles.query.all()
    return render_template('articles.html', articles=article)

#Get articles by id
@app.route('/article/<string:id>/')
def article(id):
    artticle1 = db.engine.execute('select * from articles where id=%s', [id])
    return render_template('article.html', articles=artticle1)

class RegisterForm(Form):
    name = StringField('Name', [validators.length(min=1, max=50)])
    username = StringField('Username', [validators.length(min=4, max=25)])
    email = StringField('Email', [validators.length(min=6, max=50)])
    password = StringField('Password', [
        validators.data_required(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('Confirm Password')

#User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        data = Users(name=name, email=email, username=username, password=password)
        db.session.add(data)
        db.session.commit()
        flash('You are now registered you can login', 'success')
        return redirect(url_for('articles'))
    return render_template('register.html', form=form)


# @login_manager.user_loader
# def user_loader(user_id):
#     """Given *user_id*, return the associated User object.
#
#     :param unicode user_id: user_id (email) user to retrieve
#
#     """
#     return Users.query.get(user_id)


#User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        data = Users(username=username, password=password_candidate)

        session['logged in'] = True
        session['username'] = username
        flash('You are now logged in', 'success')
        return redirect(url_for('dashboard'))

        return redirect(url_for("articles"))
    return render_template("login.html", form=form)

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorizes, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
# @is_logged_in  retuired to access dashoard
def dashboard():
    article = Articles.query.all()
    return render_template('dashboard.html', articles=article )

#Create Articles  using Wtforms
class ArticleForm(Form):
    title = StringField('Title', [validators.length(min=1, max=200)])
    body = TextAreaField('Body', [validators.length(min=30)])

@app.route('/add_article', methods=['GET', 'POST'])
# @is_logged_in  retuired to add articles
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        data = Articles(title=title, body=body, author=session['username'], date_created=datetime.now())
        db.session.add(data)
        db.session.commit()
        flash('Articles added successfully', 'success')
        # return '<h1> title: {} body:{}</h1>'.format(title, body)  # log files to check if its added successfully
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)


@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
# @is_logged_in  retuired to add articles
def edit_article(id):
    form = ArticleForm(request.form)
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        db.engine.execute('UPDATE articles SET title=%s, body=%s, author=%s, date_created=%s WHERE id=%s',
                          (title, body, session['username'], datetime.now(), id))
        # alternative update query
        # updateArticle = Articles.query.filter_by(id=id).first()
        # updateArticle.title = title
        # updateArticle.body = body
        # updateArticle.author = session['username']
        # updateArticle.date_created = datetime.now()
        db.session.commit()


        flash('Articles edited' 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)

#dDelete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
# @is_logged_in
def delete_article(id):
    db.engine.execute('DELETE FROM articles WHERE id = %s', [id])
    db.session.commit()
    flash('Articles deleted successfully' 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
