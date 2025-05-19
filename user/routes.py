from flask import render_template, url_for, redirect, request, session, flash
from db import db
from models import UserModel
from werkzeug.security import check_password_hash, generate_password_hash
from . import user_bp

#signup route
@user_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        fullname = request.form.get('fullname')
        password = generate_password_hash(request.form.get('password'))

        #if user exists
        if UserModel.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('user.signup'))

        new_user = UserModel(username=username, fullname=fullname, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('You can now login')
        return redirect(url_for('user.login'))

    return render_template('signup.html')

#login route
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = db.session.execute(db.select(UserModel).filter_by(username=username)).scalar_one_or_none()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("index.home"))
        return redirect(url_for("user.login"))
    return render_template('login.html')

#logout route
@user_bp.route('/logout')
def logout():
    session.clear()  #to log out the user
    return redirect(url_for('index.home'))
