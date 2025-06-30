# Builtins
from logging import info, error

# External
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from forms import LoginForm, PasswordChangeForm
from flask_login import login_user, login_required, logout_user

# Internal
from passwords import pw_check, pw_hash
from db import User

# TODO: Move templates
UserAuth = Blueprint('UserAuth', __name__)

@UserAuth.route('/login', methods=["GET", "POST"])
def login():

    if request.method == "GET":
        # Saves the last URL, but prevents the user from staying on the logging page
        # if the first login attempt fails
        if request.referrer and not request.referrer.endswith('/login'):
            session['login_next'] = request.referrer
        return render_template('auth/login.j2', form=LoginForm())

    form = LoginForm()
    if not form.validate_and_flash():
        return redirect(url_for('UserAuth.login'))

    user = User.get_or_none(User.nickname == form.username.data)
    if user is None or not pw_check(form.password.data, user.password):
        flash('Nesprávné uživatelské jméno nebo heslo')
        return redirect(url_for('UserAuth.login'))

    if user.temp_pw:
        session['PRE_LOGIN_UID'] = user.id
        return redirect(url_for('UserAuth.pw_change'))
    login_user(user)
    referrer = session['login_next']

    del session['login_next']
    return redirect(referrer or url_for('index'))


@UserAuth.route('/user/logout')
@login_required
def logout():
    logout_user()
    flash('Uživatel odhlášen')
    return redirect(request.referrer or url_for('index'))

@UserAuth.route('/user/pw_change', methods=["GET", "POST"])
def pw_change():

    if 'PRE_LOGIN_UID' not in session:
        return redirect(url_for('index'))

    if request.method == "GET":
        return render_template('auth/pw_change.j2', form=PasswordChangeForm())
    
    form = PasswordChangeForm()

    if not form.validate_and_flash():
        return redirect(url_for('UserAuth.pw_change'))

    user = User.get_or_none(User.id == session['PRE_LOGIN_UID'])
    if user is None:
        error("Invalid auth state (Temporary PW change in progress but user not found)")
        return redirect(url_for('index'))
    user.password = pw_hash(form.pw.data)
    user.temp_pw = False
    user.save()

    login_user(user)
    del session['PRE_LOGIN_UID']
    info(f"Permanent password created for {user.nickname} (ID: {user.id})")
    return redirect(url_for('index'))

@UserAuth.route('/user/new/pw')
def temp_pw():

    if 'tpw' not in session:
        return redirect(url_for('UserAuth.login'))

    user = User.get_or_none(User.id == session['tmp_uid'])
    if user is None:
        error("Invalid auth state (Created administrator with invalid ID)")
        return redirect(url_for('index'))

    tpw = session['tpw']
    del session['tpw']
    del session['tmp_uid']
    return render_template('auth/temp_pw.j2', user=user, tpw=tpw)
