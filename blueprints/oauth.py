from flask import flash, Blueprint, redirect, url_for, request, abort, current_app as c
from flask_discord import DiscordOAuth2Session
from flask_login import login_user
from oauthlib.oauth2.rfc6749.errors import OAuth2Error
from logging import error, warning, info
from db import Database

OauthController = Blueprint('OauthController', __name__)

@OauthController.route('/oauth/session')
def oauth_session():
    oauth: DiscordOAuth2Session = c.config['oauth']

    return oauth.create_session()

@OauthController.route('/oauth/callback')
def oauth_callback():
    oauth: DiscordOAuth2Session = c.config['oauth']
    dbs: Database = c.config['database']

    try:
        oauth.callback()
        uid = oauth.fetch_user().id
    except OAuth2Error as e:
        error(f'Oauth Failed: {str(e)}')
        flash('Autentizace selhala, zkuste to prosím znovu.')
        return redirect(url_for('UserAuth.login'))
    
    usr = dbs.get_user_by_discord(uid)
    if not usr:
        warning(f'Login attempt with unregistered ID {uid} from {request.remote_addr}')
        flash('Uživatel není registrován nebo má neplatné ID')
        return redirect(url_for('UserAuth.login'))
    
    if not usr.can_login:
        warning(f'Login attempt by unauthorized user {usr.nickname} from {request.remote_addr}')
        flash('Přihlášení je povolené pouze moderátorům')

    login_user(usr)
    return redirect(url_for('index'))   # TODO: Pamatovat si posledni URL i tady