from flask import Blueprint, current_app as c, url_for, redirect, session, request, render_template, abort, flash
from forms import NewUserForm, EditUserForm
from flask_login import current_user, login_required
from models.user import User
from logging import info

UserController = Blueprint('UserController', __name__)

@UserController.route('/user/new', methods=["GET", "POST"])
@login_required
def add_user():
    # TODO: Entering string as discord ID breaks the app and has to be manually dropped
    dbs = c.config['database']

    if request.method == "GET":
        return render_template('add_user.j2', form=NewUserForm())
    form = NewUserForm()
    u = User(0, form.nickname.data, form.wikidot.data, None, form.discord.data, not form.exempt.data, True)
    uid, tpw = dbs.add_user(u, form.can_login.data)
    if form.can_login.data:
        info(f"Administrator account created for {form.nickname.data} with ID {uid} by {current_user.nickname} (ID: {current_user.uid})")
    else:
        info(f"User account created for {form.nickname.data} with ID {uid} by {current_user.nickname} (ID: {current_user.uid})")
    session['tpw'] = tpw
    session['tmp_uid'] = uid
    return redirect(url_for('UserAuth.temp_pw') if form.can_login.data else url_for('UserController.user', uid=uid))

@UserController.route('/user/<int:uid>/edit', methods=["GET", "POST"])
@login_required
def edit_user(uid: int):
    dbs = c.config['database']

    u = dbs.get_user(uid) or abort(404)

    if request.method == "GET":
        fdata = {'nickname': u.nickname, 'wikidot': u.wikidot, 'discord': u.discord, 'exempt': not int(u.exempt), 'login': int(u.password is not None)}
        return render_template('edit_user.j2', form=EditUserForm(data=fdata), user=u)
    
    form = EditUserForm()
    un = User(uid, form.nickname.data, form.wikidot.data, u.password, form.discord.data, u.exempt, u.temp_pw)
    dbs.update_user(un)
    info(f"User {un.nickname} (ID: {uid}) edited by {current_user.nickname} (ID: {current_user.uid})")
    return redirect(url_for('user', uid=uid))

@UserController.route('/user/<int:uid>')
def user(uid: int):
    dbs = c.config['database']

    user=dbs.get_user(uid) or abort(404)
    return render_template('user.j2', user=user, stats=dbs.get_user_stats(uid), translations=dbs.get_translations_by_user(uid))

@UserController.route('/user/<int:uid>/delete', methods=["POST"])
@login_required
def delete_user(uid: int):
    dbs = c.config['database']

    name = dbs.get_user(uid).nickname
    dbs.delete_user(uid)
    info(f"User {name} deleted by {current_user.nickname} (ID: {current_user.uid})")
    flash(f'Uživatel {name} smazán')
    
    return redirect(url_for('index'))