# Builtins
from datetime import datetime
from http import HTTPStatus
from logging import info

# External
from flask import Blueprint, flash, redirect, request, render_template, abort, url_for, session, current_app
from flask_login import current_user, login_required

# Internal
from forms import NewArticleForm, EditArticleForm, AssignCorrectionForm
from models.article import Article
from models.user import get_user_role
from extensions import dbs, rss, webhook

ArticleController = Blueprint('ArticleController', __name__)

def notify_rolemaster(uid, point_amount):
    current_points = dbs.get_user_point_count(uid)
    current_role = get_user_role(current_points)
    next_role = get_user_role(current_points + point_amount)
    if current_role != next_role:
        promoted_user = dbs.get_user(uid)
        if promoted_user.discord:
            webhook.send_text(f'Uživatel {promoted_user.nickname} (<@{promoted_user.discord}>) dosáhl hranice pro roli {next_role}!')

@ArticleController.route('/article/<int:aid>/delete', methods=["POST"])
@login_required
def delete_article(aid: int):
    name = dbs.get_article(aid).name
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
        return render_template('add_translation.j2', form=form, user=dbs.get_user(uid))
    
    form = NewArticleForm()
    if not form.validate_and_flash():
        return redirect(url_for('ArticleController.add_article', uid=uid))

    title = form.title.data.upper() if form.title.data.lower().startswith('scp') else form.title.data # Capitalize SCP

    if dbs.translation_exists(title):
        flash('Překlad již existuje!')
        return redirect(url_for('ArticleController.add_article', uid=uid))
    
    if current_app.config['WEBHOOK_ENABLE']:
        notify_rolemaster(uid, form.words.data / 1000 + form.bonus.data)

    article = Article(0, title, form.words.data, form.bonus.data, datetime.now(), dbs.get_user(uid), link=form.link.data, is_original=bool(request.args.get('original', False)))
    article_id = dbs.add_article(article)
    
    if 'NEW_FROM_RSS' in session:
        del session['NEW_FROM_RSS']
        rss.remove_update(session['RSS_UUID'])
        del session['RSS_UUID']
        info(f"Article {article.name} (ID: {article_id}) added from RSS by {current_user.nickname} (ID: {current_user.uid})")
    else:
        info(f"Article {article.name} (ID: {article_id}) added by {current_user.nickname} (ID: {current_user.uid})")
    
    return redirect(url_for('UserController.user', uid=uid))

@ArticleController.route('/article/<int:aid>/edit', methods=["GET", "POST"])
@login_required
def edit_article(aid: int):

    article = dbs.get_article(aid)
    if not article:
        abort(HTTPStatus.NOT_FOUND)

    if request.method == "GET":
        fdata = {'title': article.name, 'words': article.words, 'bonus': article.bonus, 'link': article.link, 'translator': article.author.nickname}
        return render_template('edit_article.j2', form=EditArticleForm(data=fdata))
    
    form = EditArticleForm()
    if not form.validate_and_flash():
        return redirect(url_for('UserController.user', uid=article.author.get_id()))

    title = form.title.data.upper() if form.title.data.lower().startswith('scp') else form.title.data
    new_article = Article(article.id, title, form.words.data, form.bonus.data, article.added, article.author, article.corrector, article.corrected, form.link.data, article.is_original)
    dbs.update_article(new_article)
    info(f"Article {new_article.name} (ID: {aid}) edited by {current_user.nickname} (ID: {current_user.uid})")

    return redirect(url_for('UserController.user', uid=article.author.get_id()))

@ArticleController.route('/article/assign-correction', methods=["POST"])
@login_required
def assign_correction():
    form = AssignCorrectionForm()
    back_to_changes = redirect(url_for('RssPageController.rss_changes'))
    try:
        article = dbs.get_article(form.article_id.data)
    except:
        flash('Neplatné ID')
        return back_to_changes
    if not article:
        flash('Neplatné ID')
        return back_to_changes

    corrector = dbs.get_user(form.corrector_id.data)
    if not corrector:
        flash('Nastala chyba, zkuste to znovu')
        return back_to_changes

    dbs.assign_corrector(article, corrector)
    rss.remove_update(form.guid.data)
    article.link = form.link.data
    article.name = form.title.data
    dbs.update_article(article)
    flash('Článek aktualizován')
    return back_to_changes

