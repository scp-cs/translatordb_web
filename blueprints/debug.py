from flask import Blueprint, redirect, url_for
from flask_login import login_required

from extensions import dbs, sched

DebugTools = Blueprint('DebugTools', __name__)

@DebugTools.route('/debug/nickupdate')
@login_required
def nickupdate():
    dbs.update_discord_nicknames()
    return redirect(url_for('index'))

@DebugTools.route('/debug/avupdate')
@login_required
def avdownload():
    sched.run_job('Download avatars')
    return redirect(url_for('index'))

@DebugTools.route('/debug/rssupdate')
@login_required
def updaterss():
    sched.run_job('Fetch RSS updates')
    return redirect(url_for('index'))