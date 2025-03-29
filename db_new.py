import datetime
from peewee import *
from flask_login import UserMixin

database = SqliteDatabase("data/scp.db")

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

class Frontpage(ViewModel):
    user = ForeignKeyField(User, field='id', column_name='id')
    translation_count = IntegerField()
    points = FloatField()
    correction_count = IntegerField()
    original_count = IntegerField()

models = [User, Article, Backup, Note, UserType, UserHasType]