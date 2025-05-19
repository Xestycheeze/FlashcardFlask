from flask import render_template, url_for, redirect, request, session, flash
from db import db
from models import UserModel, SetModel, CardModel
from werkzeug.security import check_password_hash, generate_password_hash
from . import quiz_bp
import random

#quiz routes/select the sets
@quiz_bp.route('/select_sets', methods=['GET', 'POST'])
def select_quiz_sets():
    if request.method == 'POST':
        selected_set_ids = request.form.getlist('set_ids')
        return redirect(url_for('quiz.start_quiz', set_ids=','.join(selected_set_ids)))

    if session.get("user_id"):
        user_sets = SetModel.query.filter_by(user_id=session["user_id"]).all()
        return render_template("select_sets.html", sets=user_sets)
    return redirect(url_for("user.login"))

#quiz routes/quiz
@quiz_bp.route('/start')
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

    return redirect(url_for("user.login"))