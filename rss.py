# Builtins
from typing import List
import re
from logging import debug, info, error, warning
from datetime import datetime
from dataclasses import dataclass
from uuid import uuid4, UUID
from flask import Flask

# External
import feedparser

r_title = re.compile(r"\"(.+)\".+", re.UNICODE)

# TODO: Move this to config, possibly create separate config for RSS feeds
NEW_PAGE = 'nová stránka'   # This text in the title indicates a new page

@dataclass
class RSSUpdate:
    timestamp: datetime
    link: str
    title: str
    uuid: UUID

class RSSMonitor:
    
    def __init__(self, links: List[str] = []):
        self.__links = links
        self.__lastupdate = datetime.now()
        self.__updates = list()

    def init_app(self, app: Flask):
        if 'RSS_MONITOR_CHANNELS' not in app.config:
            warning('RSSMonitor has no endpoints!')
            return
        self.__links = app.config['RSS_MONITOR_CHANNELS']
        info(f'Loaded {len(self.__links)} RSSMonitor endpoints from config')

    def check(self):
        info(f'Fetching {len(self.__links)} RSS feeds')
        if not self.__links:
            return
        count = 0
        for link in self.__links:
            try:
                feed = feedparser.parse(link)
            except Exception as e:
                error(f"RSS Update failed for feed {link} ({e})")
            for f in feed['entries']:
                if NEW_PAGE not in f['title']:
                    continue
                timestamp = datetime.strptime(f['published'], "%a, %d %b %Y %H:%M:%S +%f")
                if timestamp > self.__lastupdate:
                    self.__updates.append(RSSUpdate(timestamp, f['link'], r_title.search(f['title']).group(1), uuid4()))
                    count += 1
            if len(self.__updates) > 0:
                self.__lastupdate = sorted(self.__updates, key=lambda a: a.timestamp, reverse=True)[0].timestamp
            else:
                self.__lastupdate = datetime.now()
        info(f'Got {count} new pages from RSS feeds')

    @property
    def updates(self) -> List[RSSUpdate]:
        return self.__updates

    @property
    def update_count(self) -> int:
        return len(self.__updates)
    
    @property
    def has_links(self) -> bool:
        return len(self.__links) > 0

    def flush_updates(self) -> None:
        self.__updates.clear()