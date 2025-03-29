from http import HTTPStatus
from peewee import IntegrityError
from flask import Blueprint, url_for, redirect, session, request, render_template, abort, flash
from forms import NewUserForm, EditUserForm
from flask_login import current_user, login_required
from db_new import Correction, User
from logging import info
from connectors.discord import DiscordClient
from passwords import pw_hash
from tasks import discord_tasks
from secrets import token_urlsafe

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

    user = User()
    user.nickname = form.nickname.data
    user.wikidot = form.wikidot.data
    user.discord = form.discord.data

    if form.can_login.data:
        temp_password = token_urlsafe(8)
        user.password = pw_hash(temp_password)
    try:
        user.save()
    except IntegrityError:
        flash("Uživatel již existuje!")
        return redirect(url_for('UserController.add_user'))

    # Fetch nickname and profile in background
    # !TODO: This is now broken because of discord client class rewrite
    sched.add_job('Immediate nickname update', lambda: discord_tasks.update_nicknames_task(override_users=[user]))
    sched.add_job('Immediate profile update', lambda: discord_tasks.download_avatars_task(override_ids=[form.discord.data]))
    
    if form.can_login.data:
        session['tpw'] = temp_password
        session['tmp_uid'] = user.get_id()
        info(f"Administrator account created for {form.nickname.data} with ID {user.get_id()} by {current_user.nickname} (ID: {current_user.get_id()})")
    else:
        info(f"User account created for {form.nickname.data} with ID {user.get_id()} by {current_user.nickname} (ID: {current_user.get_id()})")
    
    return redirect(url_for('UserAuth.temp_pw') if form.can_login.data else url_for('UserController.user', uid=user.get_id()))

@UserController.route('/user/<int:uid>/edit', methods=["GET", "POST"])
@login_required
def edit_user(uid: int):
    user = User.get_or_none(User.id == uid) or abort(HTTPStatus.NOT_FOUND)

    if request.method == "GET":
        fdata = {'nickname': user.nickname, 'wikidot': user.wikidot, 'discord': user.discord, 'login': int(user.password is not None)}
        return render_template('edit_user.j2', form=EditUserForm(data=fdata), user=user)
    
    form = EditUserForm()
    if not form.validate_and_flash():
        return redirect(url_for('UserController.edit_user', uid=uid))

    user.nickname = form.nickname.data
    user.wikidot = form.wikidot.data
    user.discord = form.discord.data
    user.save()

    info(f"User {user.nickname} (ID: {uid}) edited by {current_user.nickname} (ID: {current_user.get_id()})")
    return redirect(url_for('UserController.user', uid=uid))

@UserController.route('/user/<int:uid>')
def user(uid: int):
    sort = request.args.get('sort', 'latest', str)
    page = request.args.get('p', 0, int)
    user = User.get_or_none(User.id == uid) or abort(HTTPStatus.NOT_FOUND)
    # TODO: Sorting!
    corrections = list(Correction.select().where(Correction.corrector == user.get_id()))
    translations = dbs.get_translations_by_user(uid, sort, page)
    originals = dbs.get_originals_by_user(uid)
    return render_template('user.j2', user=user, stats=dbs.get_user_stats(uid), translations=translations, corrections=corrections, originals=originals, sort=sort)

@UserController.route('/user/<int:uid>/delete', methods=["POST", "GET"])
@login_required
def delete_user(uid: int):
    user = dbs.get_user(uid) or abort(HTTPStatus.NOT_FOUND)
    name = user.nickname
    dbs.delete_user(uid)
    info(f"User {name} deleted by {current_user.nickname} (ID: {current_user.uid})")
    flash(f'Uživatel {name} smazán')
    
    return redirect(url_for('index'))
