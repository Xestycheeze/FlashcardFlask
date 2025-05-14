from flask import Flask, render_template, url_for, redirect, request, session, flash
from pathlib import Path
from db import db
from models import UserModel, SetModel, CardModel
from werkzeug.security import check_password_hash, generate_password_hash
#flask + database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcard_flask.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.instance_path = Path("./data").resolve()
#manage user login+logout
app.secret_key = 'supersecretkey'

db.init_app(app)

#home page route
@app.route('/home')
@app.route('/')
def home():
    user_id = session.get("user_id")
    user = None
    if user_id:
        user = db.session.execute(
            db.select(UserModel).where(UserModel.id == user_id)
        ).scalar_one_or_none()
    context = {
        "user" : user,
        "users": UserModel.query.all()
    }
    return render_template("home.html", **context)

#view sets from our databse
@app.route('/sets', methods=['GET'])
def show_sets():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    user_sets = SetModel.query.filter_by(user_id=session.get("user_id")).all()
    return render_template("sets.html", sets=user_sets)

#create a new set
@app.route('/create_set', methods=['GET', 'POST'])
def create_sets():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    if request.method == 'POST':
        user = db.session.execute(db.select(UserModel).where(UserModel.id == session.get("user_id"))).scalar_one_or_none()
        name = request.form.get('name')
        new_set = SetModel(name=name, user_id=user.id)
        db.session.add(new_set)
        db.session.commit()
        return redirect(url_for('show_sets'))
    return render_template("create_sets.html")

#view cards
@app.route('/sets/set/<int:set_id>', methods=['GET'])
def show_set_cards(set_id):
    set_data = SetModel.query.get_or_404(set_id)
    return render_template("set_cards.html", set_name=set_data.name, cards=set_data.cards)

@app.route('/sets/set/<int:set_id>/card/<int:card_id>', methods=['GET', 'PATCH'])
def update_card(set_id):
    set_data = SetModel.query.get_or_404(set_id)
    return render_template("set_cards.html", set_name=set_data.name, cards=set_data.cards)


#create a new card for the 1st set
@app.route('/create_cards', methods=['GET', 'POST'])
def create_cards():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    user = db.session.execute(db.select(UserModel).where(UserModel.id == session.get("user_id"))).scalar_one_or_none()
    print(user)
    user_sets = SetModel.query.filter_by(user_id=user.id).all()

    no_set = True # query yields no sets

    if len(user_sets) > 0:
        no_set = False
        first_set = user_sets[0]

    if request.method == 'POST' and not no_set:
        front = request.form.get('front')
        back = request.form.get('back')
        set_id = request.form.get('set_id')
        
        new_card = CardModel(front=front, back=back, set_id=set_id)
        db.session.add(new_card)
        db.session.commit()
        return redirect(url_for('show_set_cards', set_id=set_id))

    return render_template("create_cards.html", no_set=no_set, user_sets=user_sets)

#signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        fullname = request.form.get('fullname')
        password = generate_password_hash(request.form.get('password'))

        #if user exists
        if UserModel.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('signup'))

        new_user = UserModel(username=username, fullname=fullname, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('You can now login')
        return redirect(url_for('login'))

    return render_template('signup.html')

#login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = db.session.execute(db.select(UserModel).filter_by(username=username)).scalar_one_or_none()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("home"))
        return redirect(url_for("login"))
    return render_template('login.html')

#logout route
@app.route('/logout')
def logout():
    session.clear()  #to log out the user
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True, port=8000, use_reloader=True)