from flask import Blueprint, url_for, redirect, session, request, render_template, abort, flash
from forms import NewUserForm, EditUserForm
from flask_login import current_user, login_required
from models.user import User
from logging import info
from connectors.discord import DiscordClient
from tasks import discord_tasks

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

    user = User(0, form.nickname.data, form.wikidot.data, None, form.discord.data, True)

    user_id, temp_password = dbs.add_user(user, form.can_login.data)
    user.uid = user_id

    # Fetch nickname and profile in background
    # !TODO: This is now broken because of discord client class rewrite
    sched.add_job('Immediate nickname update', lambda: discord_tasks.update_nicknames_task(override_users=[user]))
    sched.add_job('Immediate profile update', lambda: discord_tasks.download_avatars_task(override_ids=[form.discord.data]))
    
    if form.can_login.data:
        info(f"Administrator account created for {form.nickname.data} with ID {user_id} by {current_user.nickname} (ID: {current_user.uid})")
    else:
        info(f"User account created for {form.nickname.data} with ID {user_id} by {current_user.nickname} (ID: {current_user.uid})")
    session['tpw'] = temp_password
    session['tmp_uid'] = user_id
    return redirect(url_for('UserAuth.temp_pw') if form.can_login.data else url_for('UserController.user', uid=user_id))

@UserController.route('/user/<int:uid>/edit', methods=["GET", "POST"])
@login_required
def edit_user(uid: int):
    user = dbs.get_user(uid) or abort(404)

    if request.method == "GET":
        fdata = {'nickname': user.nickname, 'wikidot': user.wikidot, 'discord': user.discord, 'login': int(user.password is not None)}
        return render_template('edit_user.j2', form=EditUserForm(data=fdata), user=user)
    
    form = EditUserForm()
    if not form.validate_and_flash():
        return redirect(url_for('UserController.edit_user', uid=uid))

    new_user = User(uid, form.nickname.data, form.wikidot.data, user.password, form.discord.data, user.temp_pw)
    dbs.update_user(new_user)
    info(f"User {new_user.nickname} (ID: {uid}) edited by {current_user.nickname} (ID: {current_user.uid})")
    return redirect(url_for('UserController.user', uid=uid))

@UserController.route('/user/<int:uid>')
def user(uid: int):
    sort = request.args.get('sort', 'latest', str)
    page = request.args.get('p', 0, int)
    user = dbs.get_user(uid) or abort(404)
    corrections = dbs.get_corrections_by_user(uid)
    translations = dbs.get_translations_by_user(uid, sort, page)
    originals = dbs.get_originals_by_user(uid)
    return render_template('user.j2', user=user, stats=dbs.get_user_stats(uid), translations=translations, corrections=corrections, originals=originals, sort=sort)

@UserController.route('/user/<int:uid>/delete', methods=["POST", "GET"])
@login_required
def delete_user(uid: int):
    name = dbs.get_user(uid).nickname
    dbs.delete_user(uid)
    info(f"User {name} deleted by {current_user.nickname} (ID: {current_user.uid})")
    flash(f'Uživatel {name} smazán')
    
    return redirect(url_for('index'))