from db import db
from sqlalchemy import String, Integer
from sqlalchemy.orm import mapped_column, relationship

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