from flask import Flask, render_template, url_for, redirect, request, session, flash
from pathlib import Path
from db import db
from models.user import UserModel
from models.set import SetModel
from models.card import CardModel

#flask + database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#manage user login+logout
app.secret_key = 'supersecretkey'

db.init_app(app)


#home page route
@app.route('/home')
@app.route('/')
def home():
    users = UserModel.query.all()
    return render_template("home.html", users=users)

#view sets from our databse
@app.route('/sets', methods=['GET'])
def show_sets():
    all_sets = SetModel.query.all()
    return render_template("sets.html", sets=all_sets)

#create a new set
@app.route('/create_set', methods=['GET', 'POST'])
def create_sets():
    if request.method == 'POST':
        name = request.form.get('name')
        first_user = UserModel.query.first()

        if not first_user:
            return "Sign up first!", 400
        new_set = SetModel(name=name, user_id=first_user.id)
        db.session.add(new_set)
        db.session.commit()
        return redirect(url_for('show_sets'))
    return render_template("create_sets.html")

#view cards
@app.route('/sets/set/<int:set_id>', methods=['GET'])
def show_set_cards(set_id):
    set_data = SetModel.query.get_or_404(set_id)
    return render_template("set_cards.html", set_name=set_data.name, cards=set_data.cards)

#create a new card for the 1st set
@app.route('/create_cards', methods=['GET', 'POST'])
def create_cards():
    first_set = SetModel.query.first()
    no_set = False #at least we have 1 set

    if not first_set:
        no_set = True

    if request.method == 'POST' and not no_set:
        front = request.form.get('front')
        back = request.form.get('back')
        
        new_card = CardModel(front=front, back=back, set_id=first_set.id)
        db.session.add(new_card)
        db.session.commit()
        return redirect(url_for('show_set_cards', set_id=first_set.id))

    return render_template("create_cards.html", no_set=no_set)

#signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        fullname = request.form.get('fullname')
        password = request.form.get('password')

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

        user = UserModel.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.id  #save user ID
            session['username'] = user.username
            flash('Logged in')
            return redirect(url_for('home'))
        else:
            flash('Invalid username/ password')
            return redirect(url_for('login'))

    return render_template('login.html')

#logout route
@app.route('/logout')
def logout():
    session.clear()  #to log out the user
    flash('Logged out!')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=8000, use_reloader=True)