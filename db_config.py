from database import db, Theme, Story
from web_request import Parser
import time


def update_db():
    t1 = time.time()
    print("Update started at: ", time.ctime(t1))
    db.connect()
    theme_parser = Parser('https://www.rbc.ru/story/')
    themes = theme_parser.find_stories()
    for theme in themes:
        if not Theme.select().where(Theme.name == theme):
            Theme.create(name=theme, pub_date=themes[theme][0], url=themes[theme][1])
        story_parser = Parser(themes[theme][1])
        stories = story_parser.find_stories()
        for story in stories:
            # print(stories[story][0])
            old_story = Story.select().where((Story.name == story) & (Story.last_upd < stories[story][0]))
            if old_story:
                old_story = old_story[0]
            if not Story.select().where(Story.name == story):
                old_story = Story.create(name=story, theme=theme, url=stories[story][1])
            if old_story:
                article_parser = Parser(stories[story][1])
                parsed_article = article_parser.parse_story()
                old_story.last_upd = stories[story][0]
                old_story.tags = parsed_article[0]
                old_story.text = parsed_article[1]
                old_story.save()
    db.close()
    t2 = time.time()
    print("Time of update: ", t2 - t1)
