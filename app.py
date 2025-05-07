from flask import Flask, render_template, url_for, redirect, request
from pathlib import Path

from db import db #tomoro's implementation. not yet fully understood
from models import user, set, card # set and card are "unused" but are necessary to correctly define the SQLite DB schema

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcard_flask.db'
app.instance_path = Path("./data").resolve()
# db = SQLAlchemy(app)
db.init_app(app) #tomoro's implementation. not yet fully understood
@app.route('/home')
@app.route('/')
def home():
    statement = db.select(user.UserModel)
    users = db.session.execute(statement).scalars()
    return render_template("home.html", users=users)

# Make the following routes: /sets (to display all sets, method=GET), /sets/create_sets (to create sets, method=POST), /sets/set/<int:set_id> (to display all cards in a specific set, method=GET)
# Please make the database, so that Kate can start creating routes thx

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True, port=8000)
