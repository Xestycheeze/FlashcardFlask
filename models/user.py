from db import db
from sqlalchemy import String, Integer
from sqlalchemy.orm import mapped_column, relationship
from flask import session

class UserModel(db.Model):
    __tablename__ = 'Users'
    id = mapped_column(Integer, primary_key=True)
    username = mapped_column(String(15), unique=True, nullable=False)
    fullname = mapped_column(String(255))
    password = mapped_column(String(94), nullable=False)  # Assuming hashed password storage

    # Relationships
    sets = relationship('SetModel', backref='user', lazy=True, cascade='all, delete-orphan')
    #categories = db.relationship('CategoryModel', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'
    
    @classmethod
    def get_loggedin_user(cls):
        user_id = session.get("user_id")
        if not user_id:
            return None
        return db.session.execute(db.select(cls).where(cls.id==user_id)).scalar()
    
    @classmethod
    def get_all_users(cls):
        return db.session.execute(db.select(cls)).scalars()