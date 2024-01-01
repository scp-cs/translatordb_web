from db import Database
from rss import RSSMonitor
from flask_apscheduler import APScheduler
from flask_login import LoginManager
from flask_discord import DiscordOAuth2Session

dbs = Database()
rss = RSSMonitor()
sched = APScheduler()
login_manager = LoginManager()
oauth = DiscordOAuth2Session()