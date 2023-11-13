from flask import jsonify, request, current_app as c, Blueprint, abort
from flask_login import current_user
import json

SearchController = Blueprint('SearchController', __name__)

@SearchController.route('/api/search/article_any')
def search_article():
    dbs = c.config['database']

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
    dbs = c.config['database']

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
        'result': results
    })

@SearchController.route('/api/search/user')
def search_user():
    dbs = c.config['database']

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