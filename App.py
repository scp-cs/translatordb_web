# Builtins
import json
from logging import info, warning, error
import logging
from os import environ as env, makedirs

# External
from flask import Flask, render_template, request
from werkzeug.serving import is_running_from_reloader
from flask_login import current_user
from waitress import serve

# Initialize logger before importing internal modules
logging.basicConfig(filename='translatordb.log', filemode='a', format='[%(asctime)s] %(levelname)s: %(message)s', encoding='utf-8')
logging.getLogger().setLevel(logging.INFO)
handler_st = logging.StreamHandler()
handler_st.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
logging.getLogger().addHandler(handler_st)

# Internal
from models.user import get_user_role, User
from passwords import pw_hash
from utils import ensure_config
from discord import DiscordClient

# Blueprints
from blueprints.auth import UserAuth
from blueprints.debug import DebugTools
from blueprints.content import UserContent
from blueprints.errorhandler import ErrorHandler
from blueprints.users import UserController
from blueprints.articles import ArticleController
from blueprints.stats import StatisticsController
from blueprints.search import SearchController
from blueprints.rsspage import RssPageController
from blueprints.oauth import OauthController

from extensions import login_manager, dbs, rss, sched, oauth

app = Flask(__name__)

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

def extensions_init():
    login_manager.session_protection = "basic"
    login_manager.login_view = "UserAuth.login"
    login_manager.user_loader(lambda uid: dbs.get_user(uid))
    login_manager.init_app(app)

    rss.init_app(app)
    
    # Checking if we can enable Discord Login
    appid, appsecret = app.config.get('DISCORD_CLIENT_ID', None), app.config.get('DISCORD_CLIENT_SECRET', None)
    app.config['OAUTH_ENABLE'] = app.config.get('DISCORD_LOGIN_ENABLE', True)
    if not appid or not appsecret:
        warning('OAuth App ID or secret not set, Discord login disabled')
        app.config['OAUTH_ENABLE'] = False

    if app.config['OAUTH_ENABLE']:
        oauth.init_app(app)

    # Check if we are running inside Flask's auto reloader yet
    # This doesn't matter when deployed but can break things when debugging
    if is_running_from_reloader() or not app.config['DEBUG']:
        sched.init_app(app)
        sched.start()

    # Checking if we can enable the API connection
    token = app.config.get('DISCORD_TOKEN', None)
    if token:
        DiscordClient.init_app(app)
        sched.add_job('Download avatars', lambda: DiscordClient.download_avatars([u.discord for u in dbs.users()], './temp/avatar'), trigger='interval', days=3)
        sched.add_job('Fetch nicknames', lambda: dbs.update_discord_nicknames(), trigger='interval', days=4)
    else:
        warning('Discord API token not set. Profiles won\'t be updated!')

    # Checking if we have any RSS feeds configured
    if rss.has_links:
        sched.add_job('Fetch RSS updates', rss.check, trigger='interval', hours=1)


# TODO: App factory??
if __name__ == '__main__':
    
    # Load config file or create it if there isn't one
    ensure_config('config.json')
    app.config.from_file('config.json', json.load)

    # Ensure we have a directory to store the avatar thumbnails
    makedirs('./temp/avatar', exist_ok=True)

    # Store all the singleton classes in config to access them from blueprints
    app.config['database'] = dbs
    app.config['scheduler'] = sched
    app.config['oauth'] = oauth
    app.config['rss'] = rss

    # Add useful template globals
    app.add_template_global(get_user_role)
    app.add_template_global(current_user, 'current_user')
    
    # Load all the blueprints
    app.register_blueprint(ErrorHandler)
    app.register_blueprint(UserContent)
    app.register_blueprint(UserAuth)
    app.register_blueprint(DebugTools)
    app.register_blueprint(UserController)
    app.register_blueprint(ArticleController)
    app.register_blueprint(StatisticsController)
    app.register_blueprint(SearchController)
    app.register_blueprint(OauthController)
    app.register_blueprint(RssPageController)

    # Create the admin user
    user_init()
    
    extensions_init()

    # Force oauthlib to allow insecure HTTP when debugging
    if app.config['DEBUG']:
        logging.getLogger().setLevel(logging.DEBUG)
        warning('App running in debug mode!')
        env['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
        warning('OAUTHLIB insecure transport is enabled!')
        app.run('0.0.0.0', 8080)
    else:
        info("Init complete. Starting WSGI server now.")
        # TODO: Check out the task queue warnings
        serve(app, threads=8)