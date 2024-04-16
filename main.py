from flask import Flask, render_template, redirect, request
from data import db_session
from forms.reg_form import RegisterForm
from data.users import User
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, logout_user, login_user
from forms.log_form import LoginForm
from data.tasks import Task

app = Flask(__name__)
app.debug = True
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
db_session.global_init("db/task_app.db")
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/planer/', methods=['GET', 'POST'])
def planer():
    if request.method == 'GET':
        n = datetime.datetime.now

        return render_template('planer.html', planer_list=['h1', 'hhh2', 'hjhg'],
                               datetime_now=datetime.datetime.now().strftime('%d %B %A'))



if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')