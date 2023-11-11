# Builtins
import json
import sqlite3
from datetime import datetime
import typing as t
from collections import namedtuple
from logging import error, warning, critical
import time
from secrets import token_urlsafe

# External

# Internal
from models.user import User
from passwords import pw_check, pw_hash
from models.translation import Translation
from discord import DiscordClient

# Scripts
db_create_script = """

CREATE TABLE IF NOT EXISTS User (
    id          INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    nickname    TEXT        NOT NULL UNIQUE,
    wikidot     TEXT        NOT NULL UNIQUE,
    password    BLOB        DEFAULT NULL,
    discord     TEXT        ,
    exempt      BOOLEAN     NOT NULL DEFAULT 0,
    temp_pw     BOOLEAN     DEFAULT 1,
    display_name    TEXT    DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS Translation (
    id          INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    name        TEXT        NOT NULL,
    words       INTEGER     NOT NULL,
    bonus       INTEGER     NOT NULL,
    added       DATETIME    NOT NULL DEFAULT (datetime('now','localtime')),
    link        TEXT                 DEFAULT NULL,
    idauthor    INTEGER     NOT NULL,
    FOREIGN KEY (idauthor) REFERENCES User(id)
);

CREATE TABLE IF NOT EXISTS Note (
    id          INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    title       TEXT        NOT NULL,
    content     TEXT        NOT NULL,
    idauthor    INTEGER     NOT NULL,
    FOREIGN KEY (idauthor) REFERENCES User(id)
);

CREATE VIEW IF NOT EXISTS Frontpage AS
    SELECT User.id AS id, User.nickname AS nickname, User.discord AS discord, User.wikidot AS wikidot, User.display_name as display, COUNT(Translation.id) AS translation_count, (TOTAL(Translation.words)/1000.0)+TOTAL(Translation.bonus) AS points
FROM USER
LEFT JOIN Translation ON User.id = Translation.idauthor
GROUP BY User.nickname;

"""

StatRow = namedtuple('StatRow', "id nickname discord wikidot display count points")

class Database():
    
    def __init__(self, filepath: str = "data/scp.db") -> None:

        try:
            self.connection = sqlite3.connect(filepath, check_same_thread=False)
            self.__tryexec(db_create_script, script=True)
        except Exception as e:
            critical(f'Error opening database {filepath} ({str(e)})')
            raise RuntimeError(str(e))

        self.__mark_updated()

    def __tryexec(self, query: str, data: t.Tuple = (), script=False) -> sqlite3.Cursor:
        try:
            with self.connection as con:
                cur = con.cursor()
                return cur.executescript(query) if script else cur.execute(query, data)
        except sqlite3.Error as e:
            error(f'Database query "{query}" aborted with error: {str(e)}')

    def __mark_updated(self) -> None:
        query = "SELECT MAX(added) FROM Translation"
        try:
            self.__lastupdate = datetime.strptime(self.__tryexec(query).fetchone()[0], "%Y-%m-%d %H:%M:%S")
        except TypeError:
            warning(f"Unable to get last update timestamp")
            self.__lastupdate = datetime(2005, 1, 1)

    @property
    def lastupdated(self) -> datetime:
        return self.__lastupdate

    def get_stats(self, sort='points'):
        match sort:
            case 'az':
                sorter = 'ORDER BY nickname COLLATE NOCASE ASC'
            case 'points':
                sorter = 'ORDER BY points DESC'
            case 'count':
                sorter = 'ORDER BY translation_count DESC'
            case _:
                sorter = 'ORDER BY nickname COLLATE NOCASE ASC'
        data = self.__tryexec("SELECT * FROM Frontpage " + sorter).fetchall()
        return [StatRow(*row) for row in data]

    def update_password(self, uid: int, new_pw: bytes):
        query = "UPDATE User SET password=?, temp_pw=0 WHERE id=?"
        data = (new_pw, uid)
        self.__tryexec(query, data)

    def get_user(self, uid: int) -> t.Optional[User]:
        query = "SELECT * FROM User WHERE id=?"
        data = (uid,)
        row = self.__tryexec(query, data).fetchone()
        if row is None:
            return None
        return User(*row)

    def user_exists(self, username: str) -> bool:
        query = "SELECT * FROM User WHERE nickname=?"
        data = (username,)
        if not self.__tryexec(query, data).fetchone():
            return False
        else:
            return True
    
    def get_user_stats(self, uid: int) -> t.Type[StatRow]:
        return StatRow(*self.__tryexec("SELECT * FROM Frontpage WHERE id=?", (uid,)).fetchone())
    
    def verify_login(self, username: str, password: str) -> t.Optional[int]:
        query = "SELECT id, nickname, password, temp_pw FROM User WHERE nickname=?"
        cur = self.__tryexec(query, (username,))
        row = cur.fetchone()
        if not row or not row[2]:
            return None
        if not pw_check(password, row[2]):
            return None
        return row[0]

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
    
    def update_translation(self, t: Translation):
        query = "UPDATE Translation SET name=?, words=?, bonus=?, link=? WHERE id=?"
        data = (t.name, t.words, t.bonus, t.link, t.id)
        self.__tryexec(query, data)

    def update_user(self, u: User):
        query = "UPDATE User SET nickname=?, wikidot=?, discord=?, password=? WHERE id=?"
        data = (u.nickname, u.wikidot, u.discord, u.password, u.uid)
        self.__tryexec(query, data)

    # TODO: Calling an API adapter in a database class is absolutely horrible
    def update_discord_nicknames(self):
        query = "SELECT discord FROM User"
        cur = self.__tryexec(query)
        ids = cur.fetchall()
        users = dict()
        for id_ in ids:
            users[id_[0]] = DiscordClient.get_global_username(id_[0])
            time.sleep(0.2) # Wait a bit so the API doesn't 429
        for uid, nickname in users.items():
            self.__tryexec("UPDATE User SET display_name=? WHERE discord=?", (nickname, uid))

    def update_nickname(self, uid):
        nick = DiscordClient.get_global_username(uid)
        self.__tryexec("UPDATE User SET display_name=? WHERE discord=?", (nick, uid))

    def translation_exists(self, name: str):
        query = "SELECT * FROM Translation WHERE name=? COLLATE NOCASE"
        cur = self.__tryexec(query, (name.lower(),))
        if len(cur.fetchall()) != 0:
            return True
        else:
            return False

    def get_translations_by_user(self, uid: int):
        query = "SELECT * FROM Translation WHERE idauthor=? ORDER BY added DESC, id DESC"
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
        rowid = self.__tryexec(query, data).lastrowid
        self.__mark_updated()
        return rowid

    def add_user(self, u: User, gen_password=False) -> t.Tuple[int, t.Optional[str]]:
        query = "INSERT INTO User (nickname, wikidot, password, discord, exempt) VALUES (?, ?, ?, ?, ?)"
        if gen_password:
            tpw = token_urlsafe(8)
            password = pw_hash(tpw)
        else:
            tpw = None
            password = u.password
        return (self.__tryexec(query, (u.nickname, u.wikidot, password, u.discord, u.exempt)).lastrowid, tpw)