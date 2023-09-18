# Builtins
from typing import List
import re
from logging import debug, info, error, warning
from datetime import datetime
from dataclasses import dataclass
from uuid import uuid4, UUID

# External
import feedparser

r_title = re.compile(r"\"(.+)\".+", re.UNICODE)

@dataclass
class RSSUpdate:
    timestamp: datetime
    link: str
    title: str
    uuid: UUID

class RSSMonitor:
    
    def __init__(self, link):
        self.__link = link
        self.__lastupdate = datetime.now()
        self.__updates = list()
        self.check()

    def check(self):
        try:
            feed = feedparser.parse(self.__link)
        except Exception as e:
            error(f"RSS Update failed ({e})")
        new = 0
        for f in feed['entries']:
            if "nová stránka" not in f['title']:
                continue
            timestamp = datetime.strptime(f['published'], "%a, %d %b %Y %H:%M:%S +%f")
            if timestamp > self.__lastupdate:
                self.__updates.append(RSSUpdate(timestamp, f['link'], r_title.search(f['title']).group(1), uuid4()))
                new += 1
        self.__lastupdate = sorted(self.__updates, key=lambda a: a.timestamp, reverse=True)[0].timestamp
        info(f'RSS Update found {new} new pages')

    @property
    def updates(self) -> List[RSSUpdate]:
        return self.__updates

    @property
    def update_count(self) -> int:
        return len(self.__updates)

    def flush_updates(self) -> None:
        self.__updates.clear()