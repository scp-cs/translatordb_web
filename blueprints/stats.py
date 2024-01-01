from flask import render_template, Blueprint
from extensions import dbs

StatisticsController = Blueprint('StatisticsController', __name__)

@StatisticsController.route('/stats')
def view_stats():
    return render_template('stats.j2', series_info=dbs.get_series_info(), global_stats=dbs.get_global_stats())