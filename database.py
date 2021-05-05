from peewee import *

db = SqliteDatabase('rbc_stories.db')


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


db.create_tables([Theme, Story])
db.close()
