# Builtins
import json
import queue
import sqlite3
from datetime import datetime
import typing as t
import os
import errno
from os.path import exists
from translation import Translation
from collections import namedtuple

from user import User
from passwords import hashpw, pw_hash
from secrets import token_urlsafe
import re

# External

# Internal

# Scripts
db_create_script = """

DROP TABLE IF EXISTS User;
CREATE TABLE User (
    id          INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    nickname    TEXT        NOT NULL UNIQUE,
    wikidot     TEXT        NOT NULL UNIQUE,
    password    BLOB        DEFAULT NULL,
    discord     TEXT        ,
    exempt      BOOLEAN     NOT NULL DEFAULT 0
);

DROP TABLE IF EXISTS Translation;
CREATE TABLE Translation (
    id          INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    name        TEXT        NOT NULL,
    words       INTEGER     NOT NULL,
    bonus       INTEGER     NOT NULL,
    added       DATETIME    NOT NULL DEFAULT (datetime('now','localtime')),
    link        TEXT                 DEFAULT NULL,
    idauthor    INTEGER     NOT NULL,
    FOREIGN KEY (idauthor) REFERENCES User(id)
);

DROP VIEW IF EXISTS Frontpage;
CREATE VIEW Frontpage AS
    SELECT User.id AS id, User.nickname AS nickname, User.discord AS discord, User.wikidot AS wikidot, COUNT(Translation.id) AS translation_count, (TOTAL(Translation.words)/1000.0)+TOTAL(Translation.bonus) AS points
FROM USER
LEFT JOIN Translation ON User.id = Translation.idauthor
GROUP BY User.nickname;

"""

StatRow = namedtuple('StatRow', "id nickname discord wikidot count points")

class Database():
    
    def __init__(self, filepath: str = "data/scp.db", drop: bool = False) -> None:

        try:
            self.connection = sqlite3.connect(filepath, check_same_thread=False)
        except Exception as e:
            print(f'Error opening database {filepath} ({str(e)})')

        if drop:
            self.__tryexec(db_create_script, script=True)

    def migratejson(self, filepath = "translations.json", pw_for_all = False, no_users=False):
        jsons = {}
        usr_add_query = "INSERT INTO User (nickname, wikidot, password, discord, exempt) VALUES (?, ?, ?, ?, ?)"
        tr_add_query = "INSERT INTO Translation (name, words, bonus, link, idauthor) VALUES (?, ?, ?, ?, ?)"
        with open(filepath, "r") as jfile:
            jsons = json.load(jfile)
        for nick, user in jsons.items():
            a: bool
            if not no_users:
                if not pw_for_all:
                    a = input(f'Adding {nick}. Generate password? [Y/N]: ').lower() == 'y'
                else:
                    a = True
                if a:
                    pw = token_urlsafe(8)
                    print(f"PASSWORD FOR {nick}: {pw}")
                    hashed = pw_hash(pw)
                else:
                    hashed = None
            else:
                hashed = None
            lastid = self.__tryexec(usr_add_query, (nick, user['wikidot'], hashed, user['discord_id'], int(nick == "Uty"))).lastrowid
            for name, data in user['articles'].items():
                if data['wd_link'] == "NULL":
                    m = re.match(r'^(SCP-)?\d{3,4}(-J|-EX)?$', name)
                    if m:
                        if not m.string.lower().startswith('scp-'):
                            data['wd_link'] = f'http://scp-cs.wikidot.com/scp-{m.string.lower()}'
                        else:
                            data['wd_link'] = f'http://scp-cs.wikidot.com/{m.string.lower()}'

                self.__tryexec(tr_add_query, (name, data['word_count'], data['bonus_points'], data['wd_link'] if data['wd_link'] != "NULL" else None, lastid))

    def __tryexec(self, query: str, data: t.Tuple = (), script=False) -> sqlite3.Cursor:
        try:
            with self.connection as con:
                cur = con.cursor()
                if script:
                    result = cur.executescript(query)
                else:
                    result = cur.execute(query, data)
                return result
        except sqlite3.Error as e:
            print(f'Database query {query} aborted with error: {str(e)}')

    def get_stats(self, sort='az'):
        match sort:
            case 'az':
                sorter = 'ORDER BY nickname ASC'
            case 'points':
                sorter = 'ORDER BY points DESC'
            case 'count':
                sorter = 'ORDER BY translation_count DESC'
        data = self.__tryexec("SELECT * FROM Frontpage " + sorter).fetchall()
        return [StatRow(*row) for row in data]

    def update_password(self, uid: int, new_pw: bytes):
        query = "UPDATE User SET password=? WHERE id=?"
        data = (new_pw, uid)
        self.__tryexec(query, data)

    def get_user(self, uid: int) -> t.Optional[User]:
        query = "SELECT * FROM User WHERE id=?"
        data = (uid,)
        row = self.__tryexec(query, data).fetchone()
        if row is None:
            return None
        return User(*row)
    
    def get_user_stats(self, uid: int):
        return StatRow(*self.__tryexec("SELECT * FROM Frontpage WHERE id=?", (uid,)).fetchone())

    def delete_user(self, uid: int) -> None:
        query = "DELETE FROM User WHERE id=?"
        self.__tryexec(query, (uid, ))

    def delete_article(self, aid: int) -> None:
        query = "DELETE FROM Translation WHERE id=?"
        self.__tryexec(query, (aid, ))

    def users(self):
        query = "SELECT * FROM User"
        rows = self.__tryexec(query).fetchall()
        return [User(*row) for row in rows]

    def get_translation(self, tid: int):
        query = "SELECT * FROM Translation WHERE id=?"
        data = (tid,)
        row = self.__tryexec(query, data).fetchone()
        if row is None:
            return None
        tr = Translation(tid, row[1], row[2], row[3], datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S'), self.get_user(row[6]), row[5])
        return tr
    
    def translation_exists(self, name: str):
        query = "SELECT * FROM Translation WHERE name=? COLLATE NOCASE"
        cur = self.__tryexec(query, (name.lower(),))
        if len(cur.fetchall()) != 0:
            return True
        else:
            return False

    def get_translations_by_user(self, uid: int):
        query = "SELECT * FROM Translation WHERE idauthor=? ORDER BY added DESC"
        data = (uid,)
        rows = self.__tryexec(query, data).fetchall()
        if rows is None:
            return None
        translations = []
        for row in rows:
            translations.append(Translation(row[0], row[1], row[2], row[3], datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S'), self.get_user(row[6]), row[5]))
        return translations
    
    def add_article(self, a: Translation) -> int:
        query = "INSERT INTO Translation (name, words, bonus, added, link, idauthor) VALUES (?, ?, ?, ?, ?, ?)"
        data = (a.name, a.words, a.bonus, a.added.strftime('%Y-%m-%d %H:%M:%S'), a.link, a.author.get_id())
        return self.__tryexec(query, data).lastrowid