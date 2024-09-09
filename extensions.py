"""
This file stores singletons for extensions, database and api services
Classes are instantiated here, but are ready for use only after init_app is called in app.py
"""

from db import Database
from flask_apscheduler import APScheduler
from flask_login import LoginManager
from flask_discord import DiscordOAuth2Session
from connectors.rss import RSSMonitor
from connectors.discord import DiscordWebhook

dbs = Database()
sched = APScheduler()
login_manager = LoginManager()
oauth = DiscordOAuth2Session()
rss = RSSMonitor()
webhook = DiscordWebhook()