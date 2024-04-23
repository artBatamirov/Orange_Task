import smtplib
import os
from flask_login import current_user
from data import db_session
from data.tasks import Task
import datetime

def send_email(message):
    sender = 'artem.batamirov@gmail.com'
    password = os.getenv('EmailPassword')

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()

    try:
        server.login(sender, password)
        server.sendmail(sender, sender, f'Subject: hello user\n{message}')
        return 'the message was sent!'
    except Exception as e:
        return f'{e}'

def check_tasks():
    # if current_user.is_authenticated:
    #     db_sess = db_session.create_session()
    #     date_time = datetime.datetime.now()
    #     planer_list = db_sess.query(Task).filter(Task.user == current_user,
    #                                          Task.date == date_time.date(),
    #                                          Task.time == date_time.time()).all()
    #     print(planer_list, date_time)
    print('hiiiiiii')
