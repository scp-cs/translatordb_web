from flask import Flask, render_template, redirect, request, url_for, abort, flash, session
from collections import namedtuple
from datetime import datetime
import json

import sqlite3

from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from db import Database
from forms import *
from user import get_user_role, User
from passwords import pw_hash
from translation import Translation

from waitress import serve

dbs = Database()

app = Flask(__name__)
login_manager = LoginManager(app)

login_manager.session_protection = "strong"

@app.errorhandler(404)
def e404(e):
    return render_template('error.j2', errno=404, errtext="Not Found", errquote="Není žádná Antimemetická divize.", errlink="http://scp-cs.wikidot.com/your-last-first-day")

@app.errorhandler(403)
def e403(e):
    return render_template('error.j2', errno=403, errtext="Unauthorized", errquote="Okamžitě ukončete své spojení a zůstaňte na místě. Najdeme vás.", errlink="http://scp-cs.wikidot.com/scp-6630")

@app.errorhandler(500)
def e500(e):
    return render_template('error.j2', errno=500, errtext="Internal Server Error", errquote="VJEM: CHYBA. HYPERREALITA.", errlink="http://scp-cs.wikidot.com/scp-5500")

@login_manager.user_loader
def user_loader(id: str):
    return dbs.get_user(int(id))

@app.route('/')
def index():
    sort = request.args.get('sort', type=str, default='az')
    return render_template('users.j2', users=dbs.get_stats(sort), lastupdate=dbs.lastupdated)

@app.route('/user/<int:uid>/delete', methods=["POST"])
@login_required
def delete_user(uid: int):
    name = dbs.get_user(uid).nickname
    dbs.delete_user(uid)
    flash(f'Uživatel {name} smazán')
    return redirect(url_for('index'))

@app.route('/article/<int:aid>/delete', methods=["POST"])
@login_required
def delete_article(aid: int):
    name = dbs.get_translation(aid).name
    dbs.delete_article(aid)
    flash(f'Článek {name} smazán')
    return f"Delete article {aid}"

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form = LoginForm()
        uid = dbs.verify_login(form.username.data, form.password.data)
        if not uid:
            flash('Nesprávné uživatelské jméno nebo heslo')
            return redirect(url_for('login'))
        u = dbs.get_user(uid)
        if u.temp_pw:
            session['PRE_LOGIN_UID'] = uid
            return redirect(url_for('pw_change'))
        login_user(dbs.get_user(uid))
        return redirect(url_for('index'))
    return render_template('login.j2', form=LoginForm())


@app.route('/user/logout')
@login_required
def logout():
    logout_user()
    flash('Uživatel odhlášen')
    return redirect(url_for('index'))

@app.route('/user/<int:uid>')
def user(uid: int):
    user=dbs.get_user(uid)
    if not user:
        abort(404)
    return render_template('user.j2', user=user, stats=dbs.get_user_stats(uid), translations=dbs.get_translations_by_user(uid))

@app.route('/user/<int:uid>/new_article', methods=["GET", "POST"])
@login_required
def add_article(uid):
    if request.method == "GET":
        return render_template('add_article.j2', form=NewArticleForm(), user=dbs.get_user(uid))
    form = NewArticleForm()
    if not form.validate_on_submit():
        for e in form.errors.values():
            flash(e, category="error")
        return redirect(url_for('add_article', uid=uid))
    title = form.title.data.upper() if form.title.data.lower().startswith('scp') else form.title.data
    if dbs.translation_exists(title):
        flash('Překlad již existuje!')
        return redirect(url_for('add_article', uid=uid))
    t = Translation(0, title, form.words.data, form.bonus.data, datetime.now(), dbs.get_user(uid), form.link.data)
    dbs.add_article(t)
    return redirect(url_for('user', uid=uid))

@app.route('/article/<int:aid>/edit', methods=["GET", "POST"])
@login_required
def edit_article(aid: int):
    a = dbs.get_translation(aid)
    if not a:
        abort(404)

    if request.method == "GET":
        fdata = {'title': a.name, 'words': a.words, 'bonus': a.bonus, 'link': a.link, 'translator': a.author.nickname}
        return render_template('edit_article.j2', form=EditArticleForm(data=fdata))
    
    form = EditArticleForm()
    if form.validate_on_submit():
        title = form.title.data.upper() if form.title.data.lower().startswith('scp') else form.title.data
        t = Translation(a.id, title, form.words.data, form.bonus.data, a.added, a.author, form.link.data)
        dbs.update_translation(t)
    else:
        for e in form.errors.values():
            flash(e, category="error")
    return redirect(url_for('user', uid=a.author.get_id()))

@app.route('/user/new', methods=["GET", "POST"])
@login_required
def add_user():
    if request.method == "GET":
        return render_template('add_user.j2', form=NewUserForm())
    form = NewUserForm()
    u = User(0, form.nickname.data, form.wikidot.data, None, form.discord.data, not form.exempt.data, True)
    uid, tpw = dbs.add_user(u, form.can_login.data)
    session['tpw'] = tpw
    session['tmp_uid'] = uid
    return redirect(url_for('temp_pw') if form.can_login.data else url_for('user', uid=uid))

@app.route('/user/<int:uid>/edit', methods=["GET", "POST"])
@login_required
def edit_user(uid: int):
    u = dbs.get_user(uid)
    if not u:
        abort(403)

    if request.method == "GET":
        fdata = {'nickname': u.nickname, 'wikidot': u.wikidot, 'discord': u.discord, 'exempt': not int(u.exempt), 'login': int(u.password is not None)}
        return render_template('edit_user.j2', form=EditUserForm(data=fdata), user=u)
    
    form = EditUserForm()
    un = User(uid, form.nickname.data, form.wikidot.data, u.password, form.discord.data, u.exempt, u.temp_pw)
    dbs.update_user(un)
    return redirect(url_for('user', uid=uid))

@app.route('/user/new/pw')
def temp_pw():
    if 'tpw' not in session:
        return redirect(url_for('login'))
    u = dbs.get_user(session['tmp_uid'])
    tpw = session['tpw']
    del session['tpw']
    del session['tmp_uid']
    return render_template('temp_pw.j2', user=u, tpw=tpw)


@app.route('/user/pw_change', methods=["GET", "POST"])
def pw_change():
    if 'PRE_LOGIN_UID' not in session:
        return redirect(url_for('index'))

    if request.method == "GET":
        return render_template('pw_change.j2', form=PasswordChangeForm())
    
    form = PasswordChangeForm()
    dbs.update_password(session['PRE_LOGIN_UID'], pw_hash(form.pw.data))
    login_user(dbs.get_user(session['PRE_LOGIN_UID']))
    del session['PRE_LOGIN_UID']
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.config.from_file('config.json', json.load)
    app.add_template_global(get_user_role)
    app.add_template_global(current_user, 'current_user')
    serve(app)