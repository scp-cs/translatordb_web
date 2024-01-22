from logging import warning
from flask import Blueprint, redirect, url_for, current_app, request
from flask_login import login_required, current_user

from extensions import dbs, sched

DebugTools = Blueprint('DebugTools', __name__)

@DebugTools.before_request
def log_debug_access():
    if not current_app.config['DEBUG'] and not current_user.is_anonymous:
        warning(f'Debug endpoint {request.full_path} accessed by {current_user.nickname} (ID: {current_user.uid})')

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