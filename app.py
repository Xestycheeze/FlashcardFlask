from flask import Flask, render_template, url_for, redirect, request, session, flash
from pathlib import Path
from db import db
from models import UserModel, SetModel, CardModel
from werkzeug.security import check_password_hash, generate_password_hash
import random

#flask + database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcard_flask.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.instance_path = Path("./data").resolve()
#manage user login+logout
app.secret_key = 'supersecretkey'

db.init_app(app)

from user import user_bp
from index import index_bp
from set import set_bp
from quiz import quiz_bp
app.register_blueprint(user_bp)
app.register_blueprint(index_bp)
app.register_blueprint(set_bp)
app.register_blueprint(quiz_bp)


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True, port=8000, use_reloader=True)