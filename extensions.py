from db import Database
from flask_apscheduler import APScheduler
from flask_login import LoginManager
from flask_discord import DiscordOAuth2Session
from rss import RSSMonitor

dbs = Database()
sched = APScheduler()
login_manager = LoginManager()
oauth = DiscordOAuth2Session()
rss = RSSMonitor()