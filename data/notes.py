
from sqlalchemy import orm
import sqlalchemy
from .db_session import SqlAlchemyBase


class Note(SqlAlchemyBase):
    __tablename__ = 'notes'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    category = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    importance = sqlalchemy.Column(sqlalchemy.Integer, default=3)
    locked = sqlalchemy.Column(sqlalchemy.BOOLEAN, default=False)

    user = orm.relationship('User')