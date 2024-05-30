from flask import Blueprint, current_app as c, url_for, redirect, session, request, render_template, abort, flash
from forms import NewUserForm, EditUserForm
from flask_login import current_user, login_required
from models.user import User
from logging import info
from discord import DiscordClient

from extensions import dbs, sched

UserController = Blueprint('UserController', __name__)

@UserController.route('/user/new', methods=["GET", "POST"])
@login_required
def add_user():
    if request.method == "GET":
        return render_template('add_user.j2', form=NewUserForm())
    
    form = NewUserForm()
    if not form.validate_and_flash():
        return redirect(url_for('UserController.add_user'))

    u = User(0, form.nickname.data, form.wikidot.data, None, form.discord.data, True)
    uid, tpw = dbs.add_user(u, form.can_login.data)

    # Fetch nickname and profile in background
    sched.add_job('Immediate nickname update', lambda: dbs.update_nickname(form.discord.data))
    sched.add_job('Immediate profile update', func=lambda: DiscordClient.download_avatars([form.discord.data]))
    
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
    u = dbs.get_user(uid) or abort(404)

    if request.method == "GET":
        fdata = {'nickname': u.nickname, 'wikidot': u.wikidot, 'discord': u.discord, 'login': int(u.password is not None)}
        return render_template('edit_user.j2', form=EditUserForm(data=fdata), user=u)
    
    form = EditUserForm()
    if not form.validate_and_flash():
        return redirect(url_for('UserController.edit_user', uid=uid))

    un = User(uid, form.nickname.data, form.wikidot.data, u.password, form.discord.data, u.temp_pw)
    dbs.update_user(un)
    info(f"User {un.nickname} (ID: {uid}) edited by {current_user.nickname} (ID: {current_user.uid})")
    return redirect(url_for('UserController.user', uid=uid))

@UserController.route('/user/<int:uid>')
def user(uid: int):
    sort = request.args.get('sort', 'latest', str)
    page = request.args.get('p', 0, int)
    user=dbs.get_user(uid) or abort(404)
    return render_template('user.j2', user=user, stats=dbs.get_user_stats(uid), translations=dbs.get_translations_by_user(uid, sort, page), sort=sort)

@UserController.route('/user/<int:uid>/delete', methods=["POST", "GET"])
@login_required
def delete_user(uid: int):
    name = dbs.get_user(uid).nickname
    dbs.delete_user(uid)
    info(f"User {name} deleted by {current_user.nickname} (ID: {current_user.uid})")
    flash(f'Uživatel {name} smazán')
    
    return redirect(url_for('index'))