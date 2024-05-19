from flask import Flask, render_template, redirect, request, url_for, abort
from data import db_session
from forms.reg_form import RegisterForm
from data.users import User
import datetime
from sqlalchemy import and_, or_
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from forms.log_form import LoginForm
from forms.add_task_form import TaskForm
from data.tasks import Task
from message_control import send_email, check_tasks
from apscheduler.schedulers.background import BackgroundScheduler
import atexit


def delete_old():
    db_sess = db_session.create_session()
    last_date = datetime.datetime.now().date() - datetime.timedelta(days=7)
    tasks = db_sess.query(Task).filter(Task.date < last_date).all()
    for task in tasks:
        db_sess.delete(task)
    db_sess.commit()


app = Flask(__name__)
app.app_context().push()
app.debug = True
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
db_session.global_init("db/task_app.db")
login_manager = LoginManager()
login_manager.init_app(app)
datetime_now = datetime.datetime.now()
no_back = False
importance_val = {'низкая': 3, 'средняя': 2, 'высокая': 1}
importance_val_reverse = {3: 'низкая', 2: 'средняя', 1: 'высокая'}
os.environ['MY_EMAIL'] = '...@gmail.com' #your email
os.environ['EMAIL_PASS'] = '...' #your email password for apps
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    delete_old()


@login_manager.user_loader
def load_user(user_id):
    try:
        db_sess = db_session.create_session()
        login_manager.session_protection = 'strong'
        return db_sess.query(User).get(user_id)
    except Exception as e:
        print(e)


@app.route('/login', methods=['GET', 'POST'])
def login():
    global current_user
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/planer/")
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

def delete_task(task_id):
    db_sess = db_session.create_session()
    task = db_sess.query(Task).filter(Task.id == int(task_id)).first()
    if task:
        db_sess.delete(task)
    db_sess.commit()
    db_sess.close()
    print('deleted complete')
@app.route('/planer/', methods=['GET', 'POST'])
@login_required
def planer():
    global datetime_now
    global no_back

    if request.method == 'GET':
        planer_list = []
        db_sess = db_session.create_session()
        sort_choice = current_user.sort_choice
        if current_user.is_authenticated:
            planer_list = db_sess.query(Task).filter(Task.user == current_user, Task.date == datetime_now.date()).all()
            for i in planer_list:
                i.time = i.time.strftime('%H:%M')
                i.importance = importance_val_reverse[i.importance]
            if sort_choice == 2:
                planer_list.sort(key=lambda x: (importance_val[x.importance], x.time))
            if sort_choice == 1:
                planer_list.sort(key=lambda x: (x.time, importance_val[x.importance]))
            if sort_choice == 3:
                planer_list.sort(key=lambda x: (x.category, x.time, importance_val[x.importance]))

            planer_list.sort(key=lambda x: x.status, reverse=True)
        if current_user.is_authenticated:
            return render_template('planer.html', planer_list=planer_list,
                                   datetime_now=datetime_now.strftime('%d %B %A'), no_back=no_back, choice=sort_choice)
        else:
            return redirect("/")

    if request.method == 'POST':

        lst = list(request.form.items())
        print(lst)

        db_sess = db_session.create_session()
        for i in filter(lambda x: 'edit' in x[0], lst):
            task = db_sess.query(Task).filter(Task.id == i[0].split('_')[1]).first()
            return redirect(f'/edit_task/{i[0].split("_")[1]}')
        if request.form.get('plus') is not None:
            datetime_now += datetime.timedelta(days=1)
            if (datetime.datetime.now() - datetime_now - datetime.timedelta(days=1)).days < 6:
                no_back = False
        if request.form.get('minus') is not None:
            datetime_now -= datetime.timedelta(days=1)
            if (datetime.datetime.now() - datetime_now - datetime.timedelta(days=1)).days >= 6:
                no_back = True
        if request.form.get('backnow') is not None:
            datetime_now = datetime.datetime.now()
        if request.form.get('choice'):
            current_user.sort_choice = int(request.form.get('choice'))
            db_sess.merge(current_user)
            db_sess.commit()
        for i in filter(lambda x: 'del' in x[0], lst):
            task = db_sess.query(Task).filter(Task.id == int(i[0].split('_')[1])).first()
            if task:
                db_sess.delete(task)
            db_sess.commit()
            db_sess.close()

        current_tasks = db_sess.query(Task).filter(Task.user == current_user, Task.date == datetime_now.date()).all()
        checks = list(map(lambda x: int(x[0]), filter(lambda x: x[0].isdigit(), list(request.form.items()))))
        for item in current_tasks:
            if int(item.id) in checks:
                item.status = 'выполнено'
            else:
                item.status = 'не выполнено'
        db_sess.commit()
        db_sess.close()

        return redirect("/planer/")


@app.route('/user_page/', methods=['GET', 'POST'])
@login_required
def user_page():
    message = ''
    db_sess = db_session.create_session()
    if request.method == 'POST':
        if db_sess.query(User).filter(and_(User.id != current_user.id, or_(User.email == request.form.get('email'), User.name == request.form.get('name')))).first():
            message = 'Такой пользователь уже есть'
        else:
            current_user.name = request.form.get('name')
            current_user.email = request.form.get('email')
            db_sess.commit()
        if request.form.get('del') is not None:
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            db_sess.delete(user)
            db_sess.commit()
            logout_user()
            return redirect('/')

    return render_template('user_settings.html', name=current_user.name,
                           date=current_user.created_date.strftime('%d %m %Y %H:%M'),
                           email=current_user.email, message=message)


@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    global datetime_now

    db_sess = db_session.create_session()
    task = db_sess.query(Task).filter(Task.id == task_id, Task.user == current_user).first()

    if task:
        data = [task.title, task.category, datetime.datetime.combine(task.date, task.time),
                task.importance, task.description]
        form = TaskForm()
    else:
        abort(404)
    if request.method == 'POST':
        # if form.validate_on_submit():
        print('hi', form.data)
        if form.data.get('submit') and current_user.is_authenticated:
            print('yuyu', form.data)
            new_task = db_sess.query(Task).filter(Task.id == task_id, Task.user == current_user).first()
            new_task.title = form.title.data
            new_task.description = form.description.data
            new_task.category = form.category.data
            new_task.date = form.date_time.data.date()
            new_task.time = form.date_time.data.time()
            new_task.importance = importance_val[form.importance.data]
            db_sess.commit()
            db_sess.close()
        return redirect("/planer/")
    print(form.data)
    return render_template('add_task.html', datetime_now=datetime_now.strftime('%d %B %A'), form=form, inf=data)


@app.route('/add_task/', methods=['GET', 'POST'])
@login_required
def adding_task():
    global datetime_now
    form = TaskForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            db_sess = db_session.create_session()
            new_task = Task()
            new_task.title = form.title.data
            new_task.description = form.description.data
            new_task.category = form.category.data
            new_task.date = form.date_time.data.date()
            new_task.time = form.date_time.data.time()
            new_task.importance = importance_val[form.importance.data]
            # new_task.user_id = current_user.id
            # db_sess.add(new_task)
            current_user.tasks.append(new_task)
            db_sess.merge(current_user)
            db_sess.commit()
            db_sess.close()
            return redirect("/planer/")

    return render_template('add_task.html', datetime_now=datetime_now.strftime('%d %B %A'), form=form, inf=[])


if __name__ == '__main__':
    print('Ссылка на сайт https://48116be8-32f7-4556-98f6-93148307116e.tunnel4.com')
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler = BackgroundScheduler()
        scheduler = BackgroundScheduler()
        scheduler.add_job(check_tasks, "cron", second='0')
        scheduler.add_job(delete_old, 'cron', hour='0')
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())

    app.run(port=8080, host='127.0.0.1')
