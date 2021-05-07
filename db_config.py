import time
from web_request import Parser
from database import db, users_db, Theme, Story, User


def update_db():
    """
    Обновление базы данных сайта
    """
    t1 = time.time()
    try:
        print("Update started at: ", time.ctime(t1))
        db.connect()
        theme_parser = Parser('https://www.rbc.ru/story/')
        themes = theme_parser.find_stories()  # парсим темы
        for theme in themes:
            if not Theme.select().where(Theme.name == theme):  # если такой не было, создать
                Theme.create(name=theme, pub_date=themes[theme][0], url=themes[theme][1])
            story_parser = Parser(themes[theme][1])
            stories = story_parser.find_stories()  # парсим статьи
            for story in stories:
                old_story = Story.select().where((Story.name == story) & (Story.last_upd < stories[story][0]))
                if old_story:  # если нашли устаревшую статью
                    old_story = old_story[0]
                if not Story.select().where(Story.name == story):  # если такой не было, созадть
                    old_story = Story.create(name=story, theme=theme, url=stories[story][1])
                if old_story:
                    article_parser = Parser(stories[story][1])
                    parsed_article = article_parser.parse_story()  # парсим статью
                    old_story.last_upd = stories[story][0]  # обновляем данные в БД
                    old_story.tags = parsed_article[0]
                    old_story.text = parsed_article[1]
                    old_story.save()
        db.close()
        t2 = time.time()
        print("Time of update: ", t2 - t1)
    except Exception as e:
        print("Update failed, raised ", e)


def update_user_db(user_id):
    """
    Обновление базы данных пользователей.
    :param user_id: id пользователя
    """
    users_db.connect()
    if not User.select().where(User.user_id == user_id):  # если юзера не было, создать
        User.create(user_id=user_id, subscribed=False)
    users_db.close()
