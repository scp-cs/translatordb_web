from flask import jsonify, request, Blueprint
from flask_login import current_user

from extensions import dbs

SearchController = Blueprint('SearchController', __name__)

@SearchController.route('/api/search/article_any')
def search_article():
    query = request.args.get('q', None, str)
    if not query:
        return jsonify({
            'status': 'error',
            'result': []
        }), 400
    
    results = dbs.search_article(query)
    return jsonify({
        'status': 'OK',
        'result': results
    })

@SearchController.route('/api/search/article')
def search_user_article():
    query = request.args.get('q', None, str)
    author = request.args.get('u', None, int)
    if not query or not author:
        return jsonify({
            'status': 'error',
            'result': []
        }), 400
    
    results = dbs.search_article_by_user(query, author)
    return jsonify({
        'status': 'OK',
        'result': results,
        'has_auth': current_user.is_authenticated
    })

@SearchController.route('/api/search/user')
def search_user():
    query = request.args.get('q', None, str)
    if not query:
        return jsonify({
            'status': 'error',
            'result': []
        }), 400
    
    results = dbs.search_user(query)
    return jsonify({
        'status': 'OK',
        'result': results,
        'has_auth': current_user.is_authenticated
    })