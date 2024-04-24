import smtplib
import os
from email.mime.text import MIMEText
from flask_login import current_user
from data import db_session
from data.tasks import Task
import datetime

def send_email(getter, message):
    sender = 'artem.batamirov@gmail.com'
    password = 'zxuj aaqh bhbf ykvg'

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()

    try:
        server.login(sender, password)
        msg = MIMEText(message)
        msg['Subject'] = 'Напоминание от Orange Task'
        server.sendmail(sender, getter, msg.as_string())
        return 'the message was sent!'
    except Exception as e:
        return f'{e}'

def check_tasks():
    db_sess = db_session.create_session()
    date_time = datetime.datetime.now().replace (microsecond=0)
    planer_list = db_sess.query(Task).filter(Task.date == date_time.date(),
                                             Task.time == date_time.time()).all()
    db_sess.close()
    for task in planer_list:
        try:
            print(task.user.email)
            message = f'Задание: {task.title}\nВремя: {task.time.strftime("%H:%M")}\nКатегория: {task.category}' \
                      f'\nОписание: {task.description}\nВажность: {task.importance}'
            print(send_email(task.user.email, message))
        except Exception as e:
            print(e)



