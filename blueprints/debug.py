from flask import Blueprint, redirect, url_for, current_app as c
from flask_login import login_required
from discord import DiscordClient

DebugTools = Blueprint('DebugTools', __name__)

@DebugTools.route('/debug/nickupdate')
@login_required
def nickupdate():
    dbs = c.config['database']

    dbs.update_discord_nicknames()
    return redirect(url_for('index'))

@DebugTools.route('/debug/avupdate')
@login_required
def avdownload():
    dbs = c.config['database']

    DiscordClient.download_avatars([u.discord for u in dbs.users()], './temp/avatar')
    return redirect(url_for('index'))