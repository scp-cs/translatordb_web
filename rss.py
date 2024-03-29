# Builtins
from typing import List
import re
from logging import debug, info, error, warning, debug
from datetime import datetime, timedelta
from dataclasses import dataclass
from uuid import uuid4, UUID
from flask import Flask
from enum import IntEnum
from typing import Optional
from collections import deque

# Internal
from models.user import User

# External
import feedparser
import requests
from urllib import parse

# Extract the actual title from the feed's title element
r_title = re.compile(r"\"(.+)\".+", re.UNICODE)

# Extract the author's wikidot username from the HTML formatted description
r_user = re.compile(r'href="http:\/\/www\.wikidot\.com\/user:info\/(.+?)"', re.UNICODE)

# TODO: Move this to config, possibly create separate config for RSS feeds
NEW_PAGE = 'nová stránka'   # This text in the title indicates a new page
PAGE_RENAME = 'přesunout/přejmenovat stránku' # This text in the title indicates a page move
IGNORE_BRANCH_TAG = '-cs' # Ignore new pages that start with this tag, doesn't work for tales but I don't really care
TIMEZONE_UTC_OFFSET = timedelta(hours=2)

USER_AGENT = "SCUTTLE Crawler (https://scp-wiki.cz, v1)"

class RSSUpdateType(IntEnum):
    RSS_NEWPAGE = 0,
    RSS_RENAME = 1
    RSS_SOURCECHANGE = 2,
    RSS_DELETE = 3,
    RSS_UNKNOWN = 4

@dataclass
class RSSUpdate:
    timestamp: datetime
    link: str
    title: str
    author: User
    uuid: UUID

class RSSMonitor:
    
    def __init__(self, links: List[str] = []):
        self.__links = links
        self.__updates = list()
        self.__finished_guids = deque(maxlen=255)

    def init_app(self, app: Flask) -> None:
        if 'RSS_MONITOR_CHANNELS' not in app.config:
            warning('RSSMonitor has no endpoints!')
            return
        self.__links = app.config['RSS_MONITOR_CHANNELS']
        self.__dbs = app.config['database']

        info(f'Loaded {len(self.__links)} RSSMonitor endpoints from config')

    @staticmethod
    def get_rss_update_type(update: dict) -> RSSUpdateType:
        update_title = update['title']
        if NEW_PAGE in update_title:
            return RSSUpdateType.RSS_NEWPAGE
        elif PAGE_RENAME in update_title:
            return RSSUpdateType.RSS_RENAME
        else:
            return RSSUpdateType.RSS_UNKNOWN
        
    @staticmethod
    def en_page_exists(url: str) -> bool:
        """
        Converts a branch URL into an EN URL of the same page and checks if it exists on EN
        """
        try:
            parsed_url = parse.urlparse(url)
        except ValueError:
            error(f'Cannot parse URL "{url}"')
            return False
        parsed_url = parsed_url._replace(scheme='https')._replace(netloc='scp-wiki.wikidot.com')
        en_url = parse.urlunparse(parsed_url)
        try:
            head_result = requests.head(en_url, headers={'User-Agent': USER_AGENT})
        except requests.RequestException as e:
            error(f'Request to {en_url} failed ({str(e)})')
            return False
        match head_result.status_code:
            case 200:
                return True
            case 404:
                return False
            case _:
                warning(f'Got unusual status code ({head_result.status_code}) for URL {en_url}')
                return False
    
    def get_rss_update_author(self, update: dict) -> Optional[User]:
        update_description = update['description']
        username = r_user.search(update_description).group(1)
        debug(f"Extracted username \"{username}\"")
        user = self.__dbs.get_user_by_wikidot(username) # Spaces and underscores get replaced with dashes in the URL, there's no way around this unfortunately
        if not user: #! This is going to break if a user has two of these symbols in their name
            username = username.replace('-', ' ')
            user = self.__dbs.get_user_by_wikidot(username)
        if not user:
            username = username.replace(' ', '_')
            user = self.__dbs.get_user_by_wikidot(username)
        return user
        
    @staticmethod
    def get_rss_update_title(update: dict) -> str:
        return r_title.search(update['title']).group(1)

    @staticmethod
    def get_rss_update_timestamp(update: dict) -> datetime:
        return datetime.strptime(update['published'], "%a, %d %b %Y %H:%M:%S +%f")

    def _process_new_page(self, update) -> bool:
        timestamp = RSSMonitor.get_rss_update_timestamp(update)
        title = RSSMonitor.get_rss_update_title(update)
        author = self.get_rss_update_author(update)
        if not author:
            info('Ignoring {title} in RSS feed (couldn\'t match wikidot username {author} to a user)')
        debug(f'Check {title} with ts {timestamp}, last db update was {self.__dbs.lastupdated}')
        if title.lower().endswith(IGNORE_BRANCH_TAG):
            info(f'Ignoring {title} in RSS feed (not a translation)')
            return False
        
        if timestamp+TIMEZONE_UTC_OFFSET > self.__dbs.lastupdated:
            if self.__dbs.get_translation_by_link(update['link']):
                info(f'Ignoring {title} in RSS feed (added manually)')
                return False
            if not RSSMonitor.en_page_exists(update['link']):
                info(f'Ignoring {title} in RSS feed (EN Wiki page doesn\'t exist)')
                return False
            self.__updates.append(RSSUpdate(timestamp+TIMEZONE_UTC_OFFSET, update['link'], title, author, uuid4()))
            return True
        return False
        
    def check(self):
        info(f'Fetching {len(self.__links)} RSS feeds')
        if not self.__links:
            return
        
        count = 0
        for link in self.__links:
            try:
                feed = feedparser.parse(link).get('entries')
            except Exception as e:
                error(f"RSS Update failed for feed {link} ({e})")
                
            for update in feed:
                if update['guid'] in self.__finished_guids:
                    debug(f"Skip GUID {update['guid']}")
                    continue
                update_type = RSSMonitor.get_rss_update_type(update)
                match update_type:
                    case RSSUpdateType.RSS_NEWPAGE:
                        if self._process_new_page(update):
                            count +=1
                if update['guid'] not in self.__finished_guids:
                    debug(f"Add GUID {update['guid']}")
                    self.__finished_guids.append(update['guid'])

        info(f'Got {count or "no"} new pages from RSS feeds')

    @property
    def updates(self) -> List[RSSUpdate]:
        return self.__updates
    
    @property
    def update_count(self) -> int:
        return len(self.__updates)
    
    @property
    def has_links(self) -> bool:
        return len(self.__links) > 0
    
    def remove_update(self, uuid: str) -> Optional[str]:
        for u in self.__updates:
            if str(u.uuid).lower() == uuid.lower():
                debug(f'{u.link} mark finished (remove)')
                self.__updates.remove(u)
                return u.title
        return None

    def flush_updates(self) -> None:
        self.__updates.clear()