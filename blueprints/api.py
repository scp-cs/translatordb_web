from os import abort
from flask import jsonify, request, Blueprint
from flask_login import current_user

from extensions import dbs

ApiController = Blueprint('ApiController', __name__)

def result_ok(result):
    return jsonify({
        'status': 'OK',
        'result': result,
        'has_auth': current_user.is_authenticated
    })

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

    match article_type:
        case 'translation':
            results = [t.to_dict() for t in dbs.get_translations_by_user(uid, page=page)]
        case 'correction':
            results = [c.to_dict() for c in dbs.get_corrections_by_user(uid, page=page)]
        case 'original':
            return result_error('Not implemented yet')
        case _:
            return result_error('Invalid type')

    return result_ok(results)