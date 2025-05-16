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

#home page route
@app.route('/home')
@app.route('/')
def home():
    context = {
        "user" : UserModel.get_loggedin_user(),
        "users": UserModel.get_all_users(),
    }
    return render_template("home.html", **context)

#view sets from our databse
@app.route('/sets', methods=['GET'])
def show_sets():
    if session.get("user_id"):
        user_sets = SetModel.query.filter_by(user_id=session.get("user_id")).all()
        return render_template("sets.html", sets=user_sets)
    return redirect(url_for("login"))

#create a new set
@app.route('/sets/create_set', methods=['GET', 'POST'])
def create_sets():
    if request.method == 'POST':
        user = db.session.execute(db.select(UserModel).where(UserModel.id == session.get("user_id"))).scalar_one_or_none()
        name = request.form.get('name')
        new_set = SetModel(name=name, user_id=user.id)
        db.session.add(new_set)
        db.session.commit()
        return redirect(url_for('show_sets'))
    
    if session.get("user_id"):
        return render_template("create_sets.html")
    return redirect(url_for("login"))

#view cards
@app.route('/sets/<int:set_id>', methods=['GET'])
def show_set_cards(set_id):
    set = SetModel.query.get_or_404(set_id)
    return render_template("set_cards.html", set=set)

#create a new card for the 1st set
@app.route('/sets/create_cards', methods=['GET', 'POST'])
@app.route('/sets/<int:set_id>/create_cards', methods=['GET', 'POST'])
def create_cards(set_id=None):
    if request.method == 'POST':
        front = request.form.get('front')
        back = request.form.get('back')
        set_id = request.form.get('set_id')
        new_card = CardModel(front=front, back=back, set_id=set_id)
        db.session.add(new_card)
        db.session.commit()
        return redirect(url_for('show_set_cards', set_id=set_id))
    
    if session.get("user_id"):
        user = UserModel.get_loggedin_user()
        user_sets = SetModel.query.filter_by(user_id=user.id).all()
        if len(user_sets) < 1:
            return redirect(url_for("create_sets"))
        return render_template(
            "create_cards.html", 
            user_sets=user_sets, 
            set_id=set_id, 
            set=db.session.execute(db.select(SetModel).where(SetModel.id==set_id)).scalar()
            )
        
    return redirect(url_for("login"))

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

#quiz routes/select the sets
@app.route('/quiz/select_sets', methods=['GET', 'POST'])
def select_quiz_sets():
    if request.method == 'POST':
        selected_set_ids = request.form.getlist('set_ids')
        return redirect(url_for('start_quiz', set_ids=','.join(selected_set_ids)))
    
    if session.get("user_id"):
        user_sets = SetModel.query.filter_by(user_id=session["user_id"]).all()
        return render_template("select_sets.html", sets=user_sets)
    return redirect(url_for("login"))

#quiz routes/quiz
@app.route('/quiz/start')
def start_quiz():
    if session.get("user_id"):
        set_ids = request.args.get('set_ids', '')
        id_list = [int(sid) for sid in set_ids.split(',') if sid.isdigit()]
        cards = []
        for set_id in id_list:
            selected_set = SetModel.query.filter_by(id=set_id, user_id=session["user_id"]).first()
            if selected_set:
                cards.extend(selected_set.cards)

        random.shuffle(cards)
        return render_template("quiz.html", cards=cards)
    
    return redirect(url_for("login"))

#search route
@app.route('/search')
def search():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    query = request.args.get('query', '').strip()
    
    if not query:
        return render_template('search_results.html', results=[], query=query)
    
    user_results = UserModel.query.filter(
        UserModel.username.ilike(f'%{query}%')).all()
    
    
    set_results = SetModel.query.filter(
        SetModel.name.ilike(f'%{query}%')).filter_by(user_id=session.get("user_id")).all()
    
    card_results = CardModel.query.join(SetModel).filter(
    (CardModel.front.ilike(f'%{query}%') | CardModel.back.ilike(f'%{query}%')),
    SetModel.user_id == session.get("user_id")).all()
    
    results = {
        'users': user_results,
        'sets': set_results,
        'card': card_results
    }
    return render_template('search_results.html', results=results, query=query)


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True, port=8000, use_reloader=True)