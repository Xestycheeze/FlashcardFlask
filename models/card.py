from db import db
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import mapped_column

class CardModel(db.Model):
    __tablename__ = 'Cards'

    id = mapped_column(Integer, primary_key=True)
    front = mapped_column(String(1023), nullable=False)
    back = mapped_column(String(1023), nullable=False)
    indicator = mapped_column(Boolean, default=False)
    createdate = mapped_column(DateTime, nullable=False, default=db.func.now())
    set_id = mapped_column(Integer, ForeignKey('Sets.id'), nullable=False)

    def __repr__(self):
        return f'<Card {self.id}>'