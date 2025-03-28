from http import HTTPStatus
from logging import critical, warning, error
from flask import Blueprint, redirect, url_for, current_app, request, render_template, send_from_directory, flash, abort
from flask_login import login_required, current_user
from datetime import datetime

from extensions import sched, webhook

DebugTools = Blueprint('DebugTools', __name__)

@DebugTools.before_request
def log_debug_access():
    if not current_app.config['DEBUG'] and not current_user.is_anonymous:
        warning(f'Debug endpoint {request.full_path} accessed by {current_user.nickname} (ID: {current_user.uid})')

@DebugTools.route('/debug/nickupdate')
@login_required
def nickupdate():
    sched.run_job('Fetch nicknames')
    flash("Aktualizace spuštěna na pozadí!")
    return redirect(request.referrer or url_for('index'))

@DebugTools.route('/debug/avupdate')
@login_required
def avdownload():
    sched.run_job('Download avatars')
    flash("Aktualizace spuštěna na pozadí!")
    return redirect(request.referrer or url_for('index'))

@DebugTools.route('/debug/rssupdate')
@login_required
def updaterss():
    sched.run_job('Fetch RSS updates')
    flash("Aktualizace spuštěna na pozadí!")
    return redirect(request.referrer or url_for('index'))

@DebugTools.route('/debug')
@login_required
def debug_index():
    return render_template('debug/tools.j2')

@DebugTools.route('/debug/test_webhook')
@login_required
def webhook_testing():
    try:
        webhook.send_text('TEST MESSAGE')
        flash("Testovací webhook odeslán!")
    except Exception as e:
        flash("Testovací webhook se nepodařilo odeslat (zkontrolujte logy)")
        error(f"Sending test webhook failed with error ({str(e)})")
    return redirect(request.referrer or url_for('index'))
    
@DebugTools.route('/debug/db/export')
@login_required
def export_database():
    download_name=datetime.strftime(datetime.now(), 'scp_%d_%m_%Y.db')
    flash("Databáze exportována!")
    return send_from_directory('data', 'scp.db', as_attachment=True, download_name=download_name)

@DebugTools.route('/debug/raise_error')
@login_required
def raise_error():
    error("Error handling test")
    abort(HTTPStatus.INTERNAL_SERVER_ERROR)

@DebugTools.route('/debug/raise_critical')
@login_required
def raise_critical_error():
    critical("Critical error handling test")
    abort(HTTPStatus.INTERNAL_SERVER_ERROR)