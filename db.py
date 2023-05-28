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

from user import User
from passwords import hashpw, pw_hash
from secrets import token_urlsafe

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

DROP VIEW IF EXISTS Stats;
CREATE VIEW Stats AS
    SELECT User.nickname, COUNT(Translation.id) AS translation_count, SUM(Translation.words) AS total_words, (SUM(Translation.words)/1000.0) AS points, SUM(Translation.bonus) AS bonus
FROM User
LEFT JOIN Translation ON User.id = Translation.idauthor
GROUP BY User.nickname;

"""


class Database():
    
    def __init__(self, filepath: str = "data/scp.db", drop: bool = False) -> None:

        try:
            self.connection = sqlite3.connect(filepath, check_same_thread=False)
        except Exception as e:
            print(f'Error opening database {filepath} ({str(e)})')

        if drop:
            self.__tryexec(db_create_script, script=True)

    def migratejson(self, filepath = "translations.json", pw_for_all = False):
        jsons = {}
        usr_add_query = "INSERT INTO User (nickname, wikidot, password, discord, exempt) VALUES (?, ?, ?, ?, ?)"
        tr_add_query = "INSERT INTO Translation (name, words, bonus, link, idauthor) VALUES (?, ?, ?, ?, ?)"
        with open(filepath, "r") as jfile:
            jsons = json.load(jfile)
        for nick, user in jsons.items():
            a: bool
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
            lastid = self.__tryexec(usr_add_query, (nick, user['wikidot'], hashed, user['discord_id'], int(nick == "Uty"))).lastrowid
            for name, data in user['articles'].items():
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
        tr = Translation(tid, row[1], row[2], row[3], datetime.strptime(row[4], '%Y:%m:%d %H:%M:%S'), self.get_user(row[5]), row[6])
        return tr