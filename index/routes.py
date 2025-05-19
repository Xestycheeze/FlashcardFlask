from flask import render_template, session, redirect, request, url_for
from models import UserModel, SetModel, CardModel
from . import index_bp

#home page route
@index_bp.route('/home')
@index_bp.route('')
def home():
    context = {
        "user" : UserModel.get_loggedin_user(),
        "users": UserModel.get_all_users(),
    }
    return render_template("home.html", **context)

#search route
@index_bp.route('/search')
def search():
    if not session.get("user_id"):
        return redirect(url_for("user.login"))
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