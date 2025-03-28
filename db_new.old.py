from peewee import *

db_conn = SqliteDatabase(None)

class ModelBase(Model):
    class Meta:
        database = db_conn

class UserType(ModelBase):
    id = AutoField()
    name = CharField(64)

class User(ModelBase):
    id = AutoField()
    nickname = CharField(max_length=64)
    wikidot = CharField(max_length=100)
    password = BlobField(null=True)
    discord = CharField(max_length=22, null=True)
    temp_pw = BooleanField(default=False)
    display_name = CharField(max_length=64, null=True)

class UserHasType(ModelBase):
    user = ForeignKeyField(User, backref="types")
    user_type = ForeignKeyField(UserType, backref="users")

    class Meta:
        indexes = (
            (('user', 'type'), True)
        )

class Article(ModelBase):
    id = AutoField()
    name = CharField(255)
    words = IntegerField()
    bonus = IntegerField(default=0)
    added = TimestampField()
    corrected = TimestampField(null=True, default=None)
    link = TextField()
    author = ForeignKeyField(User, backref="articles")
    corrector = ForeignKeyField(User, backref="corrections", null=True)
    original = BooleanField(default=False)

class Backup(ModelBase):
    id = AutoField()
    date = TimestampField()
    article_count = IntegerField()
    author = ForeignKeyField(User, backref="author")
    fingerprint = CharField(16)
    sha1 = CharField(48)

class Note(ModelBase):
    id = AutoField()
    title = CharField(64)
    content = TextField()
    author = ForeignKeyField(User, backref="notes")
    related_article = ForeignKeyField(Article, backref="notes", null=True)
    related_user = ForeignKeyField(User, backref="notes", null=True)
    related_backupt = ForeignKeyField(Backup, backref="notes", null=True)

