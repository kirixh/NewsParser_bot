from peewee import *

db = SqliteDatabase('rbc_stories.db')  # БД для сайта
users_db = SqliteDatabase('rbc_bot_users.db')  # БД с пользователями бота

"""
Файл иницализирует базы данных сайта и пользоваетелей
"""


class Theme(Model):
    name = CharField()
    url = CharField()
    pub_date = DateTimeField()

    class Meta:
        database = db


class Story(Model):
    theme = CharField()
    name = CharField()
    url = CharField()
    last_upd = DateTimeField(null=True)
    text = CharField(null=True)
    tag = CharField(null=True)

    class Meta:
        database = db


class User(Model):
    user_id = IntegerField()
    subscribed = BooleanField()

    class Meta:
        database = users_db


db.create_tables([Theme, Story])
users_db.create_tables([User])
users_db.close()
db.close()
