from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, BooleanField, EmailField, SubmitField, SelectField, DateTimeLocalField
# from wtforms.fields import DateTimeField

from wtforms.validators import DataRequired
import datetime

class TaskForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Оиписание')
    category = SelectField('Категория', choices=['спорт', 'обучение', 'развлечения', 'программирование'])
    date_time = DateTimeLocalField('Дата и время')
    importance = SelectField("Важность", choices=['низкая', 'средняя', 'высокая'])
    submit = SubmitField('Создать')