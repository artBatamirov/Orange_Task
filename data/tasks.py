import datetime
from sqlalchemy import orm
import sqlalchemy
from .db_session import SqlAlchemyBase


class Task(SqlAlchemyBase):
    __tablename__ = 'tasks'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    status = sqlalchemy.Column(sqlalchemy.String, default='создано')
    category = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    time = sqlalchemy.Column(sqlalchemy.Time, nullable=True)
    importance = sqlalchemy.Column(sqlalchemy.Integer, default=3)

    user = orm.relationship('User', lazy='subquery')