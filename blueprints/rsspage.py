from flask import Blueprint, render_template, abort, redirect, url_for
from rss import RSSUpdate
from uuid import uuid4
from datetime import datetime

RssPageController = Blueprint('RssPageController', __name__)

@RssPageController.route('/changes')
def rss_changes():
    return render_template('changes.j2', changes=[RSSUpdate(datetime.now(), 'aaaaaaa', 'TEST CHANGE', uuid4())])