# Builtins
import json
from logging import info, warning, error
import logging
from os import environ as env, makedirs

# External
from flask import Flask, render_template, request
from werkzeug.serving import is_running_from_reloader
from flask_login import LoginManager, current_user
from waitress import serve
from flask_apscheduler import APScheduler
from flask_discord import DiscordOAuth2Session

# Initialize logger before importing internal modules
logging.basicConfig(filename='translatordb.log', filemode='a', format='[%(asctime)s] %(levelname)s: %(message)s', encoding='utf-8')
logging.getLogger().setLevel(logging.INFO)
handler_st = logging.StreamHandler()
handler_st.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
logging.getLogger().addHandler(handler_st)

# Internal
from db import Database
from forms import *
from models.user import get_user_role, User
from passwords import pw_hash
from utils import ensure_config
from discord import DiscordClient
from rss import RSSMonitor

# Blueprints
from blueprints.auth import UserAuth
from blueprints.debug import DebugTools
from blueprints.content import UserContent
from blueprints.errorhandler import ErrorHandler
from blueprints.users import UserController
from blueprints.articles import ArticleController

# Blueprints
from blueprints.auth import UserAuth
from blueprints.debug import DebugTools
from blueprints.content import UserContent
from blueprints.errorhandler import ErrorHandler
from blueprints.users import UserController
from blueprints.articles import ArticleController

from blueprints.oauth import OauthController

dbs = Database()
#rss = RSSMonitor()
app = Flask(__name__)
sched = APScheduler()
login_manager = LoginManager()
oauth = DiscordOAuth2Session()


login_manager.session_protection = "basic"
login_manager.login_view = "UserAuth.login"

@login_manager.user_loader
def user_loader(id: str):
    return dbs.get_user(int(id))

@app.route('/')
def index():
    sort = request.args.get('sort', type=str, default='az')
    return render_template('users.j2', users=dbs.get_stats(sort), lastupdate=dbs.lastupdated.strftime("%Y-%m-%d %H:%M:%S"))

def user_init():
    init_user, pwd = env.get("SCP_INIT_USER"), env.get("SCP_INIT_PASSWORD")
    if not init_user:
        return
    if not pwd:
        error(f"Password not specified for {init_user}")
        exit(-1)
    if dbs.user_exists(init_user):
        warning(f"Initial user {init_user} already exists")
        return
    info(f"Adding initial user {init_user}")
    dbs.add_user(User(1, init_user, "", pw_hash(pwd), ""))

# TODO: App factory??
if __name__ == '__main__':
    
    ensure_config('config.json')
    app.config.from_file('config.json', json.load)

    makedirs('./temp/avatar', exist_ok=True)

    app.config['database'] = dbs
    app.config['scheduler'] = sched
    app.config['oauth'] = oauth

    app.add_template_global(get_user_role)
    app.add_template_global(current_user, 'current_user')
    
    app.register_blueprint(ErrorHandler)
    app.register_blueprint(UserContent)
    app.register_blueprint(UserAuth)
    app.register_blueprint(DebugTools)
    app.register_blueprint(UserController)
    app.register_blueprint(ArticleController)
    app.register_blueprint(OauthController)

    user_init()
    login_manager.init_app(app)
    oauth.init_app(app)

    token = app.config.get('DISCORD_TOKEN', None)

    if token:
        DiscordClient.set_token(token)

        # Check if we are running inside the auto-reloader yet
        # This doesn't matter normally but messes stuff up in debug mode
        if is_running_from_reloader() or not app.config['DEBUG']:
            sched.init_app(app)
            sched.start()
            sched.add_job('Download avatars', lambda: DiscordClient.download_avatars([u.discord for u in dbs.users()], './temp/avatar'), trigger='interval', days=3)
            sched.add_job('Fetch nicknames', lambda: dbs.update_discord_nicknames(), trigger='interval', days=4)
    else:
        warning('Discord API token not set. Profiles won\'t be updated!')

    if app.config['DEBUG']:
        logging.getLogger().setLevel(logging.DEBUG)
        warning('App running in debug mode!')
        env['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
        warning('OAUTHLIB Insecure transport is enabled!')
        app.run('0.0.0.0', 8080)
    else:
        info("TranslatorDB init complete. Starting WSGI server now.")
        # TODO: Check out the task queue warnings
        serve(app, threads=8)