from flask import render_template, current_app as c, redirect, url_for, Blueprint

StatisticsController = Blueprint('StatisticsController', __name__)

@StatisticsController.route('/stats')
def view_stats():
    dbs = c.config['database']

    return render_template('stats.j2', series_info=dbs.get_series_info(), global_stats=dbs.get_global_stats())