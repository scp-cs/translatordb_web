import datetime
from peewee import *
from flask_login import UserMixin

database = SqliteDatabase("data/scp.db")

# TODO: Extract constant
PAGE_ITEMS = 15

class BaseModel(Model):
    class Meta:
        database = database

class ViewModel(BaseModel):
    def save():
        raise RuntimeError("Attempted to insert into an SQL View")
    
    class Meta:
        primary_key = False

# type: ignore
class User(BaseModel, UserMixin):
    id = AutoField()
    discord = TextField(null=True)
    display_name = TextField(null=True)
    nickname = TextField(unique=True)
    password = BlobField(null=True)
    temp_pw = BooleanField(default=True, null=True)
    wikidot = TextField(unique=True)

    @property
    def can_login(self) -> bool:
        return self.password != None
    
    def to_dict(self) -> dict:
        return {
        'id': self.id,
        'nickname': self.nickname,
        'wikidot': self.wikidot,
        'discord': self.discord,
        'displayName': self.display_name
    }

    class Meta:
        table_name = 'User'

class Article(BaseModel):
    id = AutoField()
    added = DateTimeField(default=datetime.datetime.now)
    bonus = IntegerField()
    corrected = DateTimeField(null=True)
    author = ForeignKeyField(column_name='idauthor', field='id', model=User, backref='articles')
    corrector = ForeignKeyField(backref='corrections', column_name='idcorrector', field='id', model=User, null=True)
    is_original = BooleanField(default=False)
    link = TextField(null=True)
    name = TextField()
    words = IntegerField()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "words": self.words,
            "bonus": self.bonus,
            "added": self.added,
            "author": self.author.to_dict(),
            "corrector": self.corrector.to_dict() if self.corrector else None,
            "corrected": self.corrected,
            "link": self.link
            }

    class Meta:
        table_name = 'Article'

class Backup(BaseModel):
    id = AutoField()
    articles = IntegerField()
    date = DateTimeField(default=datetime.datetime.now)
    fingerprint = BlobField()
    author = ForeignKeyField(column_name='idauthor', field='id', model=User, backref='backups')
    sha1 = BlobField()

    class Meta:
        table_name = 'Backup'

class Note(BaseModel):
    id = AutoField()
    content = TextField()
    author = ForeignKeyField(column_name='idauthor', field='id', model=User, backref='created_notes')
    title = TextField()
    related_article = ForeignKeyField(column_name='related_article', field='id', model=Article, backref="notes", null=True)
    related_user = ForeignKeyField(column_name='related_user', field='id', model=User, backref="notes", null=True)
    related_backup = ForeignKeyField(column_name='related_backup', field='id', model=Backup, backref="notes", null=True)

    class Meta:
        table_name = 'Note'

class UserType(BaseModel):
    id = AutoField()
    name = TextField(unique=True)

    class Meta:
        table_name = 'UserType'

class UserHasType(BaseModel):
    user_type = ForeignKeyField(column_name='idtype', field='id', model=UserType, backref='users')
    user = ForeignKeyField(column_name='iduser', field='id', model=User, backref='types')

    class Meta:
        table_name = 'UserHasType'

class Backup(BaseModel):
    id = AutoField()
    date = TimestampField()
    article_count = IntegerField()
    author = ForeignKeyField(User, backref="author")
    fingerprint = CharField(16)
    sha1 = CharField(48)

class Series(ViewModel):
    series = IntegerField()
    articles = IntegerField()
    words = IntegerField()

    class Meta:
        table_name = 'Series'

class Statistics(ViewModel):
    total_words = IntegerField()
    total_articles = IntegerField()
    total_users = IntegerField()

    class Meta:
        table_name = 'Statistics'

class Correction(ViewModel):
    article = ForeignKeyField(Article, field='id', column_name='article_id', backref='correction')
    author = ForeignKeyField(User, field='id', column_name='author')
    corrector = ForeignKeyField(User, field='id', backref='corrections', column_name='corrector')
    timestamp = DateTimeField()
    words = IntegerField()
    name = TextField()

    def to_dict(self):
        return {
            'article': self.article.to_dict(),
            'author': self.author.to_dict(),
            'corrector': self.corrector.to_dict(),
            'timestamp': self.timestamp,
            'words': self.words
        }

class Frontpage(ViewModel):
    user = ForeignKeyField(User, field='id', column_name='id', backref='stats')
    translation_count = IntegerField()
    points = FloatField()
    correction_count = IntegerField()
    original_count = IntegerField()

models = [User, Article, Backup, Note, UserType, UserHasType]

def last_update() -> datetime.datetime:
    return Article.select(fn.MAX(Article.added)).scalar()

def get_frontpage(sort: str, page: int):
    entries = Frontpage.select().join(User).limit(PAGE_ITEMS).offset(PAGE_ITEMS*page)
    match sort:
        case 'az':
            result = entries.order_by(User.nickname.collate("NOCASE").asc())
        case 'points':
            result = entries.order_by(Frontpage.points.desc())
        case 'count':
            result = entries.order_by(Frontpage.translation_count.desc())
        case 'corrections':
            result = entries.order_by(Frontpage.correction_count.desc())
        case 'originals':
            result = entries.order_by(Frontpage.original_count.desc())
        case _:
            result = entries.order_by(Frontpage.points.desc())
    return result
