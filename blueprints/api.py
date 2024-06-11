from logging import warning, info, error
from flask import jsonify, request, Blueprint, flash, redirect, url_for, abort
from flask_login import current_user, login_required

from extensions import dbs

ApiController = Blueprint('ApiController', __name__)

def result_ok(result = [], extra_data = {}):
    return jsonify({
        'status': 'OK',
        'result': result,
        'hasAuth': current_user.is_authenticated
    } | extra_data)

def result_error(error_message = "", status_code = 400):
    return jsonify({
            'status': 'error',
            'result': [],
            'errorMessage': error_message
        }), status_code

@ApiController.route('/api/search/article_any')
def search_article():
    query = request.args.get('q', None, str)
    if not query:
        return result_error("No query specified", 400)
    
    results = dbs.search_article(query)
    return result_ok(results)

@ApiController.route('/api/search/article')
def search_user_article():
    query = request.args.get('q', None, str)
    author = request.args.get('u', None, int)
    if not query or not author:
        return result_error("Parameters missing")
    
    if author == -1:
        results = dbs.search_article(query)
    else:
        results = dbs.search_article_by_user(query, author)
        
    return result_ok(results)

@ApiController.route('/api/search/user')
def search_user():
    query = request.args.get('q', None, str)
    if not query:
        return result_error("No query specified")
    
    results = dbs.search_user(query)
    return result_ok(results)

@ApiController.route('/api/user/<int:uid>')
def api_get_user(uid: int):
    user = dbs.get_user(uid)
    if not user: return result_error("User doesn't exist", 404)

    results = user.to_dict()
    return result_ok(results)

@ApiController.route('/api/user/<int:uid>/articles')
def api_get_articles(uid: int):
    user = dbs.get_user(uid)
    if not user: return result_error("User doesn't exist", 404)

    page = request.args.get("p", 0, int)
    article_type = request.args.get("t", "translation", str)
    sort = request.args.get("s", "latest", str)

    match article_type:
        case 'translation':
            results = [t.to_dict() for t in dbs.get_translations_by_user(uid, page=page, sort=sort)]
            total = dbs.get_article_counts(uid).translations[0]
        case 'correction':
            results = [c.to_dict() for c in dbs.get_corrections_by_user(uid, page=page, sort=sort)]
            total = dbs.get_article_counts(uid).corrections[0]
        case 'original':
            results = [o.to_dict() for o in dbs.get_originals_by_user(uid, page=page, sort=sort)]
            total = dbs.get_article_counts(uid).originals[0]
        case _:
            return result_error('Invalid type')

    return result_ok(results, {"total": total})

@ApiController.route('/api/user/<int:uid>/assign-correction', methods=['POST'])
@login_required
def assign_correction(uid: int):
    article_id = request.form.get('aid', None, int)
    if not article_id:
        flash('Neplatný článek')
        return result_error('Neplatný článek')
    article = dbs.get_article(article_id)
    if not article:
        flash('Neplatný článek')
        return result_error('Neplatný článek')
    corrector = dbs.get_user(uid)
    if not corrector:
        flash('Neplatný uživatel')
        return result_error('Neplatný uživatel')
    dbs.assign_corrector(article, corrector)
    info(f"Assigning correction of \"{article.name}\" ({article.id}) to {corrector.nickname} ({corrector.uid})")
    flash('Korekce zapsána')
    return result_ok()

@ApiController.route('/api/article/<int:aid>/remove-correction', methods=["POST"])
@login_required
def remove_correction(aid: int):

    article = dbs.get_article(aid)
    if not article:
        flash('Neplatný článek')
        return result_error('Neplatný článek')

    dbs.unassign_corrector(article)
    flash('Korekce odstraněna')
    return result_ok()