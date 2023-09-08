from flask import Blueprint, flash, redirect, request, render_template, abort, url_for, current_app as c
from flask_login import current_user, login_required
from forms import NewArticleForm, EditArticleForm
from logging import info
from models.translation import Translation
from datetime import datetime

ArticleController = Blueprint('ArticleController', __name__)

@ArticleController.route('/article/<int:aid>/delete', methods=["POST"])
@login_required
def delete_article(aid: int):
    dbs = c.config['database']

    name = dbs.get_translation(aid).name
    dbs.delete_article(aid)
    info(f"Article {name} deleted by {current_user.nickname} (ID: {current_user.uid})")
    flash(f'Článek {name} smazán')
    return f"Delete article {aid}"

@ArticleController.route('/user/<int:uid>/new_article', methods=["GET", "POST"])
@login_required
def add_article(uid):
    dbs = c.config['database']

    if request.method == "GET":
        return render_template('add_article.j2', form=NewArticleForm(), user=dbs.get_user(uid))
    
    form = NewArticleForm()
    if not form.validate_on_submit():
        for e in form.errors.values():
            flash(e[0], category="error")
        return redirect(url_for('ArticleController.add_article', uid=uid))
    title = form.title.data.upper() if form.title.data.lower().startswith('scp') else form.title.data
    if dbs.translation_exists(title):
        flash('Překlad již existuje!')
        return redirect(url_for('ArticleController.add_article', uid=uid))
    t = Translation(0, title, form.words.data, form.bonus.data, datetime.now(), dbs.get_user(uid), form.link.data)
    aid = dbs.add_article(t)
    info(f"Article {t.name} (ID: {aid}) added by {current_user.nickname} (ID: {current_user.uid})")
    return redirect(url_for('UserController.user', uid=uid))

@ArticleController.route('/article/<int:aid>/edit', methods=["GET", "POST"])
@login_required
def edit_article(aid: int):
    dbs = c.config['database']

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
        info(f"Article {t.name} (ID: {aid}) edited by {current_user.nickname} (ID: {current_user.uid})")
    else:
        for e in form.errors.values():
            flash(e, category="error")
    return redirect(url_for('UserController.user', uid=a.author.get_id()))