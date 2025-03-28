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

# Internal
from models.user import get_user_role, get_role_color, User
from passwords import pw_hash
from utils import ensure_config
from connectors.discord import DiscordClient
from connectors.rss import RSSUpdateType
from tasks import discord_tasks
import db_new

# Blueprints
from blueprints.auth import UserAuth
from blueprints.debug import DebugTools
from blueprints.content import UserContent
from blueprints.errorhandler import ErrorHandler
from blueprints.users import UserController
from blueprints.articles import ArticleController
from blueprints.stats import StatisticsController
from blueprints.api import ApiController
from blueprints.rsspage import RssPageController
from blueprints.oauth import OauthController
from blueprints.embed import EmbedController

from extensions import login_manager, dbs, sched, oauth, rss, webhook

app = Flask(__name__)

LOGGER_FORMAT_STR = '[%(asctime)s][%(module)s] %(levelname)s: %(message)s'

@app.route('/')
def index():
    sort = request.args.get('sort', type=str, default='points')
    page = request.args.get('p', type=int, default=0)
    user_count = dbs.get_user_count()
    return render_template('users.j2', users=dbs.get_stats(sort, page), lastupdate=dbs.lastupdated.strftime("%Y-%m-%d %H:%M:%S"), user_count=user_count, sort=sort)

def init_logger() -> None:
    """
    Sets up logging
    """
    
    logging.basicConfig(filename='translatordb.log', filemode='a', format=LOGGER_FORMAT_STR, encoding='utf-8')
    logging.getLogger().setLevel(logging.INFO)
    handler_st = logging.StreamHandler()
    handler_st.setFormatter(logging.Formatter(LOGGER_FORMAT_STR))
    logging.getLogger().addHandler(handler_st)

def fix_proxy() -> None:
    """
    Registers the ProxyFix middleware as described in https://flask.palletsprojects.com/en/3.0.x/deploying/proxy_fix/
    """
    
    if "FIX_PROXY" in app.config and app.config['FIX_PROXY']:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

def user_init() -> None:
    """
    Registers an administrator from environment variables
    """

    init_user, init_password = env.get("SCP_INIT_USER"), env.get("SCP_INIT_PASSWORD")
    if not init_user:
        return
    if not init_password:
        error(f"Password not specified for {init_user}")
        exit(-1)
    if dbs.user_exists(init_user):
        warning(f"Initial user {init_user} already exists")
        return
    info(f"Adding initial user {init_user}")
    dbs.add_user(User(1, init_user, "", pw_hash(init_password), ""))

def extensions_init() -> None:
    """
    Checks which integrations can be enabled, initializes all flask extensions and schedules background tasks
    """

    login_manager.session_protection = "basic"
    login_manager.login_view = "UserAuth.login"
    login_manager.user_loader(lambda uid: dbs.get_user(uid))
    login_manager.init_app(app)

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
    discord_token = app.config.get('DISCORD_TOKEN', None)
    if discord_token:
        DiscordClient.init_app(app)
        sched.add_job('Download avatars', lambda: discord_tasks.download_avatars_task(), trigger='interval', days=3)
        sched.add_job('Fetch nicknames', lambda: discord_tasks.update_nicknames_task(), trigger='interval', days=4)
    else:
        warning('Discord API token not set. Profiles won\'t be updated!')

    # Checking if we have a webhook URL
    webhook_url = app.config.get('DISCORD_WEBHOOK_URL', None)
    if webhook_url:
        webhook.init_app(app)
        app.config['WEBHOOK_ENABLE'] = True
    else:
        app.config['WEBHOOK_ENABLE'] = False

    rss.init_app(app)

    # Checking if we have any RSS feeds configured
    if rss.has_links:
        sched.add_job('Fetch RSS updates', rss.check, trigger='interval', hours=1)


# TODO: App factory??
if __name__ == '__main__':
    init_logger()

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
    app.config['webhook'] = webhook

    # Add useful template globals
    app.add_template_global(get_user_role)
    app.add_template_global(get_role_color)
    app.add_template_global(current_user, 'current_user')
    app.add_template_global(RSSUpdateType)
    
    # Load all the blueprints
    app.register_blueprint(ErrorHandler)
    app.register_blueprint(UserContent)
    app.register_blueprint(UserAuth)
    app.register_blueprint(DebugTools)
    app.register_blueprint(UserController)
    app.register_blueprint(ArticleController)
    app.register_blueprint(StatisticsController)
    app.register_blueprint(ApiController)
    app.register_blueprint(OauthController)
    app.register_blueprint(RssPageController)
    app.register_blueprint(EmbedController)

    # Create the admin user
    user_init()

    # Initialize the database
    db_new.database.create_tables(db_new.models)

    # Load extensions and enable integrations based on config
    extensions_init()

    # Force oauthlib to allow insecure transport when debugging
    if app.config['DEBUG']:
        logging.getLogger().setLevel(logging.DEBUG)
        warning('App running in debug mode!')
        env['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
        warning('OAUTHLIB insecure transport is enabled!')
        app.run('0.0.0.0', 8080)
    else:
        fix_proxy()
        info("Init complete. Starting WSGI server now.")
        serve(app, threads=64)