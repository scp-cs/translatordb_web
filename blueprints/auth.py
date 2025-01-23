# Builtins
from logging import info

# External
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from forms import LoginForm, PasswordChangeForm
from flask_login import login_user, login_required, logout_user

# Internal
from passwords import pw_hash
from extensions import dbs

# TODO: Move templates
UserAuth = Blueprint('UserAuth', __name__)

@UserAuth.route('/login', methods=["GET", "POST"])
def login():

    if request.method == "GET":
        # Saves the last URL, but prevents the user from staying on the logging page
        # if the first login attempt fails
        if not request.referrer.endswith('/login'):
            session['login_next'] = request.referrer
        return render_template('auth/login.j2', form=LoginForm())

    form = LoginForm()
    if not form.validate_and_flash():
        return redirect(url_for('UserAuth.login'))

    user_id = dbs.verify_login(form.username.data, form.password.data)
    if not user_id:
        flash('Nesprávné uživatelské jméno nebo heslo')
        return redirect(url_for('UserAuth.login'))
    user = dbs.get_user(user_id)
    if user.temp_pw:
        session['PRE_LOGIN_UID'] = user_id
        return redirect(url_for('UserAuth.pw_change'))
    login_user(user)
    referrer = session['login_next']
    info(referrer)
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

    dbs.update_password(session['PRE_LOGIN_UID'], pw_hash(form.pw.data))
    user = dbs.get_user(session['PRE_LOGIN_UID'])
    login_user(user)
    del session['PRE_LOGIN_UID']
    info(f"Permanent password created for {user.nickname} (ID: {user.uid})")
    return redirect(url_for('index'))

@UserAuth.route('/user/new/pw')
def temp_pw():

    if 'tpw' not in session:
        return redirect(url_for('UserAuth.login'))
    user = dbs.get_user(session['tmp_uid'])
    tpw = session['tpw']
    del session['tpw']
    del session['tmp_uid']
    return render_template('auth/temp_pw.j2', user=user, tpw=tpw)
