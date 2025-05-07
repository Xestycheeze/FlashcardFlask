from db import db
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, relationship


class SetModel(db.Model):
    __tablename__ = 'Sets'

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(255), nullable=False)
    createdate = mapped_column(DateTime, nullable=False, default=db.func.now())
    # category_id = mapped_column(Integer, ForeignKey('Category.id'), nullable=False)
    user_id = mapped_column(Integer, ForeignKey('Users.id'), nullable=False)

    # Relationships
    cards = relationship('CardModel', backref='set', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Set {self.name}>'