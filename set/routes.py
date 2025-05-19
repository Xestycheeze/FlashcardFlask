from flask import render_template, url_for, redirect, request, session, flash
from db import db
from models import UserModel, SetModel, CardModel
from werkzeug.security import check_password_hash, generate_password_hash
from . import set_bp

#view sets from our databse
@set_bp.route('', methods=['GET'])
def show_sets():
    if session.get("user_id"):
        user_sets = SetModel.query.filter_by(user_id=session.get("user_id")).all()
        return render_template("sets.html", sets=user_sets)
    return redirect(url_for("user.login"))

#create a new set
@set_bp.route('/create_set', methods=['GET', 'POST'])
def create_sets():
    if request.method == 'POST':
        user = db.session.execute(db.select(UserModel).where(UserModel.id == session.get("user_id"))).scalar_one_or_none()
        name = request.form.get('name')
        new_set = SetModel(name=name, user_id=user.id)
        db.session.add(new_set)
        db.session.commit()
        return redirect(url_for('set.show_sets'))

    if session.get("user_id"):
        return render_template("create_sets.html")
    return redirect(url_for("user.login"))

#view cards
@set_bp.route('/<int:set_id>', methods=['GET', 'POST'])
def show_set_cards(set_id):
    set_data = SetModel.query.get_or_404(set_id)
    if request.method == 'POST': # Updates name of set
        payload = request.form
        if payload and len(payload.get("new-name").strip()) > 0:
            set_data.name = payload.get("new-name").strip()
            db.session.commit()
    return render_template("set_cards.html", set_data=set_data, cards=set_data.cards)

@set_bp.route('/delete/set/<int:set_id>', methods=['POST'])
def delete_set(set_id):
    target_set = SetModel.query.get_or_404(set_id)
    try:
        # SetModel deletion was already defined to cascade onto CardModel
        db.session.delete(target_set)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('set.show_set_cards', set_id=set_id))
    return redirect(url_for('set.show_sets'))

@set_bp.route('/<int:set_id>/cards/<int:card_id>', methods=['GET', 'POST'])
def update_card(set_id, card_id):
    set_data = SetModel.query.get_or_404(set_id)
    card = CardModel.query.get_or_404(card_id)
    if set_data.user_id != session.get("user_id") or card.set_id != set_data.id:
        return redirect(url_for("set.show_sets"))
    user_sets = SetModel.query.filter_by(user_id=session.get("user_id")).all()
    if request.method == 'POST': # HTML Forms do not support PATCH, so PATCH behaviour is created manually
        payload = request.form
        if not payload:
            return redirect(url_for("set.show_set_cards", set_id=card.set_id))
        for key, value in payload.items():
            if value != "":
                if key == "set_id":
                    value = int(value)
                # This is a PATCH operation
                setattr(card, key, value)
        db.session.commit()
        return redirect(url_for("set.show_set_cards", set_id=card.set_id))

    return render_template("update_card.html", available_sets=user_sets, card=card)


#create a new card for the 1st set
@set_bp.route('/create_cards', methods=['GET', 'POST'])
@set_bp.route('/<int:set_id>/create_cards', methods=['GET', 'POST'])
def create_cards(set_id=None):
    if request.method == 'POST':
        front = request.form.get('front')
        back = request.form.get('back')
        set_id = request.form.get('set_id')
        new_card = CardModel(front=front, back=back, set_id=set_id)
        db.session.add(new_card)
        db.session.commit()
        return redirect(url_for('set.show_set_cards', set_id=set_id))

    if session.get("user_id"):
        user = UserModel.get_loggedin_user()
        user_sets = SetModel.query.filter_by(user_id=user.id).all()
        if len(user_sets) < 1:
            return redirect(url_for("set.create_sets"))
        return render_template(
            "create_cards.html",
            user_sets=user_sets,
            set_id=set_id,
            set=db.session.execute(db.select(SetModel).where(SetModel.id==set_id)).scalar()
            )

    return redirect(url_for("user.login"))


@set_bp.route('/delete/card/<int:card_id>', methods=['POST'])
def delete_card(card_id):
    flashcard = CardModel.query.get_or_404(card_id)
    try:
        set_id = flashcard.set_id
        db.session.delete(flashcard)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('set.show_sets'))
    return redirect(url_for('set.show_set_cards', set_id=set_id))
