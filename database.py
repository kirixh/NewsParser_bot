import peewee

db = peewee.SqliteDatabase('rbc_stories.db')  # БД для сайта
users_db = peewee.SqliteDatabase('rbc_bot_users.db')  # БД с пользователями бота

"""
Файл иницализирует базы данных сайта и пользоваетелей
"""


class Theme(peewee.Model):
    name = peewee.CharField()
    url = peewee.CharField()
    pub_date = peewee.DateTimeField()

    class Meta:
        database = db


class Story(peewee.Model):
    theme = peewee.CharField()
    name = peewee.CharField()
    url = peewee.CharField()
    last_upd = peewee.DateTimeField(null=True)
    text = peewee.CharField(null=True)
    tag = peewee.CharField(null=True)

    class Meta:
        database = db


class User(peewee.Model):
    user_id = peewee.IntegerField()
    subscribed = peewee.BooleanField()

    class Meta:
        database = users_db


db.create_tables([Theme, Story])
users_db.create_tables([User])
users_db.close()
db.close()
