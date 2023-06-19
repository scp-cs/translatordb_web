from flask import Flask, render_template, redirect, request, url_for, abort, flash, session
from collections import namedtuple
import json

import sqlite3

from flask_login import LoginManager, login_required
from db import Database
from forms import LoginForm, PasswordChangeForm, NewArticleForm

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
    return render_template('users.j2', users=dbs.get_stats(sort))

@app.route('/abort/<int:e>')
def error(e:int):
    abort(e)

@app.route('/user/<int:uid>/delete', methods=["POST"])
def delete_user(uid: int):
    dbs.delete_user(uid)
    return f"Delete user {uid}"

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return "OK"
    return render_template('login.j2', form=LoginForm())

@app.route('/pw_change', methods=["GET", "POST"])
def pw_change():
    if request.method == "POST":
        form = PasswordChangeForm()
        if not form.validate_on_submit():
            flash("Něco se posralo, zavolejte cheemsovi.", category="error")
            return redirect(url_for('pw_change'))
        else:
            dbs.update_password()

    return render_template('pw_change.j2')

@app.route('/user/<int:uid>')
def user(uid: int):
    user=dbs.get_user(uid)
    if not user:
        abort(404)
    return render_template('user.j2', user=user, stats=dbs.get_user_stats(uid), translations=dbs.get_translations_by_user(uid))

@app.route('/user/<int:uid>/new_article', methods=["GET", "POST"])
def add_article(uid):
    return render_template('add_article.j2', form=NewArticleForm(), user=dbs.get_user(uid))

if __name__ == '__main__':
    app.config.from_file('config.json', json.load)
    #dbs.migratejson(pw_for_all=False, no_users=True)
    app.run(debug=True)