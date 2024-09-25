from logging import warning, error
from flask import Blueprint, redirect, url_for, current_app, request, render_template, send_from_directory
from flask_login import login_required, current_user
from datetime import datetime

from extensions import dbs, sched, webhook

DebugTools = Blueprint('DebugTools', __name__)

def test_webhook() -> bool:
    try:
        webhook.send_text('TEST MESSAGE')
        return True
    except Exception as e:
        error(f"Sending test webhook failed with error ({str(e)})")
        return False

@DebugTools.before_request
def log_debug_access():
    if not current_app.config['DEBUG'] and not current_user.is_anonymous:
        warning(f'Debug endpoint {request.full_path} accessed by {current_user.nickname} (ID: {current_user.uid})')

@DebugTools.route('/debug/nickupdate')
@login_required
def nickupdate():
    sched.run_job('Fetch nicknames')
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

@DebugTools.route('/debug')
def debug_index():
    return render_template('debug/tools.j2')

@DebugTools.route('/debug/test_webhook')
def webhook_testing():
    result = test_webhook()
    if result:
        return 200
    else:
        return 500
    
@DebugTools.route('/debug/db/export')
def export_database():
    download_name=datetime.strftime(datetime.now(), 'scp_%d_%m_%Y.db')
    return send_from_directory('data', 'scp.db', as_attachment=True, download_name=download_name)