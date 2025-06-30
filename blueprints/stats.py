from flask import render_template, Blueprint
from db import Statistics, Series

StatisticsController = Blueprint('StatisticsController', __name__)

@StatisticsController.route('/stats')
def view_stats():
    return render_template('stats.j2', series_info=Series.select(), global_stats=Statistics.select().first())