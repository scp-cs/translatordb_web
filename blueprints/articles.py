# Builtins
from datetime import datetime
from logging import info

# External
from flask import Blueprint, flash, redirect, request, render_template, abort, url_for, session, current_app
from flask_login import current_user, login_required

# Internal
from forms import NewArticleForm, EditArticleForm
from models.translation import Translation
from models.user import get_user_role
from extensions import dbs, rss, webhook

ArticleController = Blueprint('ArticleController', __name__)

@ArticleController.route('/article/<int:aid>/delete', methods=["POST"])
@login_required
def delete_article(aid: int):
    name = dbs.get_translation(aid).name
    dbs.delete_article(aid)
    info(f"Article {name} deleted by {current_user.nickname} (ID: {current_user.uid})")
    flash(f'Článek {name} smazán')
    return "OK"

@ArticleController.route('/user/<int:uid>/new_article', methods=["GET", "POST"])
@login_required
def add_article(uid):

    if request.method == "GET":
        form = NewArticleForm()
        if request.args.get('rss', None):
            form.title.data = request.args.get('t')
            form.link.data = request.args.get('l')
            session['NEW_FROM_RSS'] = True
            session['RSS_UUID'] = request.args.get('u')
        return render_template('add_article.j2', form=form, user=dbs.get_user(uid))
    
    form = NewArticleForm()
    if not form.validate_and_flash():
        return redirect(url_for('ArticleController.add_article', uid=uid))

    title = form.title.data.upper() if form.title.data.lower().startswith('scp') else form.title.data
    if dbs.translation_exists(title):
        flash('Překlad již existuje!')
        return redirect(url_for('ArticleController.add_article', uid=uid))
    
    if current_app.config['WEBHOOK_ENABLE']:
        current_points = dbs.get_user_point_count(uid)
        current_role = get_user_role(current_points)
        next_role = get_user_role(current_points + form.words.data / 1000 + form.bonus.data)
        if current_role != next_role:
            promoted_user = dbs.get_user(uid)
            if promoted_user.discord:
                webhook.send_text(f'Uživatel {promoted_user.nickname} (<@{promoted_user.discord}>) dosáhl hranice pro roli {next_role}!')

    t = Translation(0, title, form.words.data, form.bonus.data, datetime.now(), dbs.get_user(uid), form.link.data)
    aid = dbs.add_article(t)
    
    if 'NEW_FROM_RSS' in session:
        del session['NEW_FROM_RSS']
        rss.remove_update(session['RSS_UUID'])
        del session['RSS_UUID']
        info(f"Article {t.name} (ID: {aid}) added from RSS by {current_user.nickname} (ID: {current_user.uid})")
    else:
        info(f"Article {t.name} (ID: {aid}) added by {current_user.nickname} (ID: {current_user.uid})")
    
    return redirect(url_for('UserController.user', uid=uid))

@ArticleController.route('/article/<int:aid>/edit', methods=["GET", "POST"])
@login_required
def edit_article(aid: int):

    a = dbs.get_translation(aid)
    if not a:
        abort(404)

    if request.method == "GET":
        fdata = {'title': a.name, 'words': a.words, 'bonus': a.bonus, 'link': a.link, 'translator': a.author.nickname}
        return render_template('edit_article.j2', form=EditArticleForm(data=fdata))
    
    form = EditArticleForm()
    if not form.validate_and_flash():
        return redirect(url_for('UserController.user', uid=a.author.get_id()))

    title = form.title.data.upper() if form.title.data.lower().startswith('scp') else form.title.data
    t = Translation(a.id, title, form.words.data, form.bonus.data, a.added, a.author, form.link.data)
    dbs.update_translation(t)
    info(f"Article {t.name} (ID: {aid}) edited by {current_user.nickname} (ID: {current_user.uid})")

    return redirect(url_for('UserController.user', uid=a.author.get_id()))