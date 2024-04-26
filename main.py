import schedule
from flask import Flask, render_template, redirect, request, url_for
from data import db_session
from forms.reg_form import RegisterForm
from data.users import User
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from forms.log_form import LoginForm
from forms.add_task_form import TaskForm
from data.tasks import Task
from  message_control import send_email, check_tasks
from apscheduler.schedulers.background import BackgroundScheduler
import atexit


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
edit_form = None
edit_val = False
os.environ['MY_EMAIL'] = 'artem.batamirov@gmail.com'
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    os.environ['EMAIL_PASS'] = input('Password:')




@login_manager.user_loader
def load_user(user_id):
    try:
        db_sess = db_session.create_session()
        return db_sess.query(User).get(user_id)
    except Exception as e:
        print(e)

@app.route('/login', methods=['GET', 'POST'])
def login():
    global  current_user
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

@app.route('/planer/', methods=['GET', 'POST'])
@login_required
def planer():
    global datetime_now
    global no_back
    global edit_val
    global edit_form

    if request.method == 'GET':
        planer_list = []
        db_sess = db_session.create_session()
        if current_user.is_authenticated:
            planer_list = db_sess.query(Task).filter(Task.user == current_user, Task.date == datetime_now.date()).all()
            for i in planer_list:
                i.time = i.time.strftime('%H:%M')
        if current_user.is_authenticated:
            return render_template('planer.html', planer_list=planer_list,
                               datetime_now=datetime_now.strftime('%d %B %A'), no_back=no_back)
        else:
            return redirect("/")

    if request.method == 'POST':
        db_sess = db_session.create_session()
        lst = list(request.form.items())
        print(lst)
        for i in filter(lambda x: 'del' in x[0], lst):
            task = db_sess.query(Task).filter(Task.id == i[0].split('_')[1]).first()
            db_sess.delete(task)
            db_sess.commit()
        for i in filter(lambda x: 'edit' in x[0], lst):
            task = db_sess.query(Task).filter(Task.id == i[0].split('_')[1]).first()
            if edit_form is None:
                edit_form = TaskForm()
            edit_form.title.data = task.title
            edit_form.description.data = task.description
            edit_form.category.data = task.category
            edit_form.importance.data = task.importance
            edit_form.date_time.data = datetime.datetime.combine(task.date, task.time)
            db_sess.delete(task)
            db_sess.commit()
            edit_val = True
            return redirect('/edit_task/')

            # total_time = datetime.datetime.combine(task.date, task.time).strftime('%d/%m/%Y/%H:%M')
            # information = ' '.join([task.title, total_time, task.category, task.importance, task.description])
            # db_sess.delete(task)
            # db_sess.commit()
            # return redirect(url_for('adding_task', add_form=information))
            # return render_template('add_task.html', datetime_now=datetime_now.strftime('%d %B %A'), form=form)
        if request.form.get('plus') is not None:
            datetime_now += datetime.timedelta(days=1)
        if request.form.get('minus') is not None:
            if (datetime.datetime.now() - datetime_now - datetime.timedelta(days=1)).days >= 6:
                no_back = True
            else:
                datetime_now -= datetime.timedelta(days=1)
                no_back = False
        if request.form.get('backnow') is not None:
            datetime_now = datetime.datetime.now()

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
    db_sess = db_session.create_session()
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.email = request.form.get('email')
        db_sess.merge(current_user)

        if request.form.get('del'):
            db_sess.delete(current_user)
            return redirect('/logout')
        db_sess.commit()

    return render_template('user_settings.html', name=current_user.name,
                           date=current_user.created_date.strftime('%d %m %Y %H:%M'),
                           email=current_user.email)

@app.route('/edit_task/', methods=['GET', 'POST'])
@login_required
def edit_task():
    global datetime_now
    global edit_form
    global edit_val
    form = TaskForm()
    if edit_val:
        data = list(edit_form)
        edit_val = False
        form.title.data = data[0].data
        form.description.data = data[1].data
        form.category.data = data[2].data
        form.date_time.data = data[3].data
        form.importance.data = data[4].data

        # form.data = edit_form.data
    # global add_form
    # if add_form is None:
    #     add_form = TaskForm()
    # # form = TaskForm()
    # # if request.args.get('add_form'):
    # #     information = request.args.get('add_form').split()
    # #     print(information)
    # #     form.title.data = information[0]
    # #     if len(information) == 5:
    # #         form.description.data = information[4]
    # #     form.category.data = information[2]
    # #     form.importance.data = information[3]
    # #     form.date_time.data = datetime.datetime.strptime(information[1], '%d/%m/%Y/%H:%M')
    if request.method == 'POST':
        # if form.validate_on_submit():
        if current_user.is_authenticated:
            print(form.data)
            db_sess = db_session.create_session()
            new_task = Task()
            new_task.title = form.title.data
            new_task.description = form.description.data
            new_task.category = form.category.data
            new_task.date = form.date_time.data.date()
            new_task.time = form.date_time.data.time()
            new_task.importance = form.importance.data
            # new_task.user_id = current_user.id
            # db_sess.add(new_task)
            current_user.tasks.append(new_task)
            db_sess.merge(current_user)
            db_sess.commit()
            db_sess.close()
        return redirect("/planer/")

    return render_template('add_task.html', datetime_now=datetime_now.strftime('%d %B %A'), form=form)

@app.route('/add_task/', methods=['GET', 'POST'])
@login_required
def adding_task():
    global datetime_now
    form = TaskForm()
    # global add_form
    # if add_form is None:
    #     add_form = TaskForm()
    # # form = TaskForm()
    # # if request.args.get('add_form'):
    # #     information = request.args.get('add_form').split()
    # #     print(information)
    # #     form.title.data = information[0]
    # #     if len(information) == 5:
    # #         form.description.data = information[4]
    # #     form.category.data = information[2]
    # #     form.importance.data = information[3]
    # #     form.date_time.data = datetime.datetime.strptime(information[1], '%d/%m/%Y/%H:%M')
    if form.validate_on_submit():
        if current_user.is_authenticated:
            db_sess = db_session.create_session()
            new_task = Task()
            new_task.title = form.title.data
            new_task.description = form.description.data
            new_task.category = form.category.data
            new_task.date = form.date_time.data.date()
            new_task.time = form.date_time.data.time()
            new_task.importance = form.importance.data
            # new_task.user_id = current_user.id
            # db_sess.add(new_task)
            current_user.tasks.append(new_task)
            db_sess.merge(current_user)
            db_sess.commit()
            db_sess.close()
            return redirect("/planer/")

    return render_template('add_task.html', datetime_now=datetime_now.strftime('%d %B %A'), form=form)



if __name__ == '__main__':


    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler = BackgroundScheduler()
        scheduler.add_job(check_tasks, "cron", second='0')
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())

    # t = Thread(target=job)
    # t.start()

    app.run(port=8080, host='127.0.0.1')


