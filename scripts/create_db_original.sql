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
    SELECT User.id AS id, User.nickname AS nickname, User.discord AS discord, User.wikidot AS wikidot, User.display_name as display, 
    SUM(CASE WHEN Article.is_original=FALSE THEN 1 ELSE 0 END) AS translation_count, 
    (SUM(CASE WHEN Article.is_original=FALSE THEN Article.words ELSE 0 END)/1000.0)+TOTAL(Article.bonus) AS points,
    (SELECT COUNT(article_id) FROM Correction WHERE Corrector=User.id) AS correction_count,
    SUM(CASE WHEN Article.is_original=TRUE THEN 1 ELSE 0 END) AS original_count
        FROM user
            LEFT JOIN Article 
                ON User.id = Article.idauthor
        GROUP BY User.id;

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
    SELECT id as article_id, idauthor AS author, idcorrector AS corrector, corrected AS timestamp, words, name
        FROM Article WHERE idcorrector IS NOT NULL;