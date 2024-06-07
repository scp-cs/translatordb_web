# Builtins
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
from models.article import Article
from models.correction import Correction
from discord import DiscordClient

PAGE_ITEMS = 15

# Scripts
db_create_script = """

CREATE TABLE IF NOT EXISTS UserType (
    id          INTEGER     NOT NULL PRIMARY KEY,
    name        TEXT        NOT NULL UNIQUE
);

INSERT OR IGNORE INTO UserType (id, name) VALUES (1, "translator"), (2, "corrector"), (3, "writer"), (4, "staff");

CREATE TABLE IF NOT EXISTS User (
    id          INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    nickname    TEXT        NOT NULL UNIQUE,
    wikidot     TEXT        NOT NULL UNIQUE,
    password    BLOB        DEFAULT NULL,
    discord     TEXT        ,
    temp_pw     BOOLEAN     DEFAULT 1,
    display_name    TEXT    DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS UserHasType (
    id          INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    iduser      INTEGER     NOT NULL,
    idtype      INTEGER     NOT NULL,
    FOREIGN KEY (iduser) REFERENCES User(id) ON DELETE CASCADE,
    FOREIGN KEY (idtype) REFERENCES UserType(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Article (
    id          INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    name        TEXT        NOT NULL,
    words       INTEGER     NOT NULL,
    bonus       INTEGER     NOT NULL,
    added       DATETIME    NOT NULL DEFAULT (datetime('now','localtime')),
    link        TEXT                 DEFAULT NULL,
    idauthor    INTEGER     NOT NULL,
    idcorrector INTEGER     DEFAULT NULL,
    corrected   DATETIME    DEFAULT NULL,
    is_original BOOLEAN     NOT NULL DEFAULT FALSE,
    FOREIGN KEY (idauthor) REFERENCES User(id) ON DELETE CASCADE,
    FOREIGN KEY (idcorrector) REFERENCES User(id)
);

CREATE TABLE IF NOT EXISTS Note (
    id          INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    title       TEXT        NOT NULL,
    content     TEXT        NOT NULL,
    idauthor    INTEGER     NOT NULL,
    FOREIGN KEY (idauthor) REFERENCES User(id) ON DELETE CASCADE
);

CREATE VIEW IF NOT EXISTS Frontpage AS
    SELECT User.id AS id, User.nickname AS nickname, User.discord AS discord, User.wikidot AS wikidot, User.display_name as display, COUNT(Article.id) AS translation_count, (TOTAL(Article.words)/1000.0)+TOTAL(Article.bonus) AS points
        FROM user
            LEFT JOIN Article 
                ON User.id = Article.idauthor
        WHERE Article.is_original = FALSE
        GROUP BY User.nickname;

CREATE VIEW IF NOT EXISTS Series AS 
    SELECT (SUBSTR(name, 5)/1000)+1 AS series, COUNT(id) AS articles, SUM(words) AS words 
        FROM Article 
        WHERE (name 
            LIKE 'SCP-___' OR name LIKE 'SCP-____') AND is_original=FALSE 
        GROUP BY SERIES
    UNION
    SELECT 999 AS series, COUNT(id) AS articles, SUM(words) AS words
        FROM Article
        WHERE name
            NOT LIKE 'SCP-___' AND name NOT LIKE 'SCP-____' AND is_original=FALSE;

CREATE VIEW IF NOT EXISTS Statistics AS
    SELECT SUM(t.words) AS total_words, COUNT(t.id) AS total_articles, (SELECT COUNT(id) FROM user) AS total_users
        FROM Article AS t WHERE t.is_original=FALSE;

CREATE VIEW IF NOT EXISTS Correction AS
    SELECT id as article_id, idauthor AS author, idcorrector AS corrector
        FROM Article WHERE idcorrector IS NOT NULL;
"""

StatRow = namedtuple('StatRow', "id nickname discord wikidot display count points")
SeriesRow = namedtuple('SeriesRow', "series articles words")
StatisticsRow = namedtuple('StatisticsRow', "total_words total_articles total_users")

class Database():
    
    def __init__(self, filepath: str = "data/scp.db") -> None:

        try:
            self.connection = sqlite3.connect(filepath, check_same_thread=False)
            self.__tryexec(db_create_script, script=True)
            # self.connection.execute('PRAGMA journal_mode=wal')  # Enable write-ahead logging
            self.connection.execute('PRAGMA foreign_keys=1')    # Enable SQLite foreign keys
        except Exception as e:
            critical(f'Error opening database {filepath} ({str(e)})')
            raise RuntimeError(str(e))

        self.__mark_updated()

    def __tryexec(self, query: str, data: t.Tuple = (), script=False) -> sqlite3.Cursor:
        try:
            with self.connection as con:
                cursor = con.cursor()
                return cursor.executescript(query) if script else cursor.execute(query, data)
        except sqlite3.Error as e:
            error(f'Database query "{query}" aborted with error: {str(e)}')

    def __mark_updated(self) -> None:
        query = "SELECT MAX(added) FROM Article"
        try:
            self.__lastupdate = datetime.strptime(self.__tryexec(query).fetchone()[0], "%Y-%m-%d %H:%M:%S")
        except TypeError:
            warning(f"Unable to get last update timestamp")
            self.__lastupdate = datetime(2005, 1, 1)

    def __make_article(self, row) -> Article:
        return Article(row[0], row[1], row[2], row[3], datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S'), self.get_user(row[6]), self.get_user(row[7]), datetime.strptime(row[9], '%Y-%m-%d %H:%M:%S'), row[5], row[8])

    @property
    def lastupdated(self) -> datetime:
        return self.__lastupdate

    def get_stats(self, sort='points', page=0):
        match sort:
            case 'az':
                sorter = 'ORDER BY nickname COLLATE NOCASE ASC'
            case 'points':
                sorter = 'ORDER BY points DESC'
            case 'count':
                sorter = 'ORDER BY translation_count DESC'
            case _:
                sorter = 'ORDER BY nickname COLLATE NOCASE ASC'
        data = self.__tryexec("SELECT * FROM Frontpage " + sorter + " LIMIT ? OFFSET ?", (PAGE_ITEMS, PAGE_ITEMS*page)).fetchall()
        return [StatRow(*row) for row in data]

    def get_user_count(self) -> int:
        count = self.__tryexec("SELECT COUNT(id) FROM Frontpage").fetchone()[0]
        return count

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
    
    def get_user_by_discord(self, dscid: int) -> t.Optional[User]:
        query = "SELECT * FROM User WHERE discord=?"
        data = (dscid,)
        row = self.__tryexec(query, data).fetchone()
        if row is None:
            return None
        return User(*row)
    
    def get_user_by_wikidot(self, wdid: str) -> t.Optional[User]:
        query = "SELECT * FROM User WHERE wikidot=? COLLATE NOCASE"
        data = (wdid,)
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
        cursor = self.__tryexec(query, (username,))
        row = cursor.fetchone()
        if not row or not row[2]:
            return None
        if not pw_check(password, row[2]):
            return None
        return row[0]

    def delete_user(self, uid: int) -> None:
        queries = [ # TODO: Maybe we shouldn't delete the articles with the user
            "DELETE FROM Article WHERE idauthor=?",
            "DELETE FROM Note WHERE idauthor=?",
            "DELETE FROM User WHERE id=?"]
        for query in queries:   # No cascade delete because I'm dumb
            self.__tryexec(query, (uid, ))

    def delete_article(self, aid: int) -> None:
        query = "DELETE FROM Article WHERE id=?"
        self.__tryexec(query, (aid, ))

    def users(self) -> t.List:
        query = "SELECT * FROM User"
        rows = self.__tryexec(query).fetchall()
        return [User(*row) for row in rows]

    def get_article(self, tid: int) -> t.Optional[Article]:
        query = "SELECT * FROM Article WHERE id=?"
        data = (tid,)
        row = self.__tryexec(query, data).fetchone()
        if row is None:
            return None
        return self.__make_article(row)
    
    def update_translation(self, t: Article) -> None:
        query = "UPDATE Article SET name=?, words=?, bonus=?, link=? WHERE id=?"
        data = (t.name, t.words, t.bonus, t.link, t.id)
        self.__tryexec(query, data)

    def assign_corrector(self, article: Article, user: User):
        query = "UPDATE Article SET idcorrector=? WHERE id=?"
        data = (user.uid, article.id)
        self.__tryexec(query, data)

    def update_user(self, u: User) -> None:
        query = "UPDATE User SET nickname=?, wikidot=?, discord=?, password=? WHERE id=?"
        data = (u.nickname, u.wikidot, u.discord, u.password, u.uid)
        self.__tryexec(query, data)

    def rename_article(self, name: str, new_name: str):
        ... # We need to update the link too

    # TODO: Calling an API adapter in a database class is absolutely horrible
    def update_discord_nicknames(self) -> None:
        query = "SELECT discord FROM User"
        ids = self.__tryexec(query).fetchall()
        users = dict()
        for id_ in ids:
            users[id_[0]] = DiscordClient.get_global_username(id_[0])
            time.sleep(0.2) # Wait a bit so the API doesn't 429
        for uid, nickname in users.items():
            self.__tryexec("UPDATE User SET display_name=? WHERE discord=?", (nickname, uid))

    def update_nickname(self, uid) -> None:
        nickname = DiscordClient.get_global_username(uid)
        self.__tryexec("UPDATE User SET display_name=? WHERE discord=?", (nickname, uid))

    def translation_exists(self, name: str) -> bool:
        query = "SELECT * FROM Article WHERE name=? COLLATE NOCASE"
        cursor = self.__tryexec(query, (name.lower(),))
        if len(cursor.fetchall()) != 0:
            return True
        else:
            return False

    def get_translations_by_user(self, uid: int, sort='latest', page=0) -> t.Optional[list[Article]]:
        match sort:
            case 'az':
                sorter = 'ORDER BY name COLLATE NOCASE ASC'
            case 'latest':
                sorter = 'ORDER BY added DESC, id DESC'
            case 'words':
                sorter = 'ORDER BY words DESC'
            case _:
                sorter = 'ORDER BY name COLLATE NOCASE ASC'
        query = "SELECT * FROM Article WHERE idauthor=? AND is_original=FALSE " + sorter + " LIMIT ? OFFSET ?"
        data = (uid, PAGE_ITEMS, page*PAGE_ITEMS)
        rows = self.__tryexec(query, data).fetchall()
        if rows is None:
            return None
        return [self.__make_article(row) for row in rows]

    def get_article_by_link(self, link: str):
        query = "SELECT * FROM Article WHERE link=?"
        data = (link,)
        row = self.__tryexec(query, data).fetchone()
        return None if not row else self.__make_article(row)
    
    def get_user_point_count(self, uid: int) -> int:
        row = self.__tryexec("SELECT points FROM Frontpage WHERE id=?", (uid,)).fetchone()
        return row[0] if row else 0

    def get_series_info(self, sid: int = 0) -> list[SeriesRow] | SeriesRow:
        query = "SELECT * FROM Series" if not sid else "SELECT * FROM SERIES WHERE series=?"
        data = self.__tryexec(query, () if not sid else (sid,)).fetchall()
        return [SeriesRow(*d) for d in data] if not sid else SeriesRow(*data[0])

    def get_global_stats(self) -> StatisticsRow:
        query = "SELECT * FROM Statistics"
        data = self.__tryexec(query).fetchone()
        return StatisticsRow(*data)
    
    def add_article(self, a: Article) -> int:
        query = "INSERT INTO Article (name, words, bonus, added, link, idauthor, is_original) VALUES (?, ?, ?, ?, ?, ?, ?)"
        data = (a.name, a.words, a.bonus, a.added.strftime('%Y-%m-%d %H:%M:%S'), a.link, a.author.get_id(), a.is_original)
        rowid = self.__tryexec(query, data).lastrowid
        self.__mark_updated()
        return rowid

    # TODO: Generate tpw in controller
    def add_user(self, u: User, gen_password=False) -> t.Tuple[int, t.Optional[str]]:
        query = "INSERT INTO User (nickname, wikidot, password, discord) VALUES (?, ?, ?, ?)"
        if gen_password:
            temp_password = token_urlsafe(8)
            password = pw_hash(temp_password)
        else:
            temp_password = None
            password = u.password
        return (self.__tryexec(query, (u.nickname, u.wikidot, password, u.discord)).lastrowid, temp_password)

    def search_user(self, param: str) -> t.List[dict]:
        query = "SELECT * FROM Frontpage WHERE nickname LIKE :param OR wikidot LIKE :param OR display LIKE :param OR discord=:param"
        results = self.__tryexec(query, {'param': f'%{param}%'}).fetchall()
        if not results:
            return list()
        return [{
            'id': result[0],
            'nickname': result[1],
            'discord': result[2],
            'wikidot': result[3],
            'displayname': result[4],
            'tr_count': result[5],
            'points': result[6]
        } for result in results]

    def search_article(self, param: str) -> t.List[Article]:    # TODO: Add parameter for translation/original
        query = "SELECT * FROM Article WHERE name LIKE :param OR link LIKE :link"
        results = self.__tryexec(query, {'param': f'%{param}%', 'link': f"%.wikidot.com/%{param}%"}).fetchall()
        search_result = []
        user_cache = {}
        for result in results:
            if result[6] not in user_cache: # Ugly but saves us a lot of queries
                author = user_cache[result[6]] = self.get_user(result[6])
            else:
                author = user_cache[result[6]]
            if not author: # Ideally, this shouldn't happen. In practice I forgot to enable foreign keys initially so it's possible
                continue
            if result[7]:
                if result[7] not in user_cache:
                    corrector = user_cache[result[7]] = self.get_user(result[7])
                else:
                    corrector = user_cache[result[7]]
            else:
                corrector = None
            search_result.append({
                'id': result[0],
                'name': result[1],
                'link': result[5],
                'words': result[2],
                'author': {
                    'id': author.uid,
                    'name': author.display_name or author.nickname
                },
                'corrector': {
                    'id': corrector.uid if corrector else 0,
                    'name': (corrector.display_name or corrector.nickname) if corrector else 'N/A'
                }
            })
        return search_result

    def search_article_by_user(self, param: str, uid: int):
        query = "SELECT * FROM Article WHERE (name LIKE :param OR link LIKE :link) AND idauthor=:uid"
        results = self.__tryexec(query, {'param': f'%{param}%', 'link': f"%.wikidot.com/%{param}%", 'uid': uid}).fetchall()
        user_cache = {}
        search_result = []
        for result in results:
            if result[7]:
                if result[7] not in user_cache:
                    corrector = user_cache[result[7]] = self.get_user(result[7])
                else:
                    corrector = user_cache[result[7]]
            else:
                corrector = None
            search_result.append({
                'id': result[0],
                'name': result[1],
                'link': result[5],
                'words': result[2],
                'bonus': result[3],
                'added': result[4],
                'corrector': {
                    'id': corrector.uid if corrector else 0,
                    'name': (corrector.display_name or corrector.nickname) if corrector else 'N/A'
                }
            })
        return search_result

    def get_corrections_by_user(self, user_id: int, page=0) -> t.Optional[t.List[Correction]]:
        user_cache = {}
        result = []
        corrector = self.get_user(user_id)
        corrections = self.__tryexec("SELECT * FROM Correction WHERE corrector=? LIMIT ? OFFSET ?", (user_id, PAGE_ITEMS, PAGE_ITEMS*page)).fetchall()
        if not corrections:
            return None
        for correction in corrections:
            article = self.get_article(correction[0])
            if correction[1] in user_cache:
                author = user_cache[correction[1]]
            else:
                author = self.get_user(correction[1])
                user_cache[correction[1]] = author
            result.append(Correction(article, author, corrector))
        return result