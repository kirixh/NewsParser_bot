import telebot
import threading
from db_config import users_db, User, update_db, update_user_db, Theme, Story
import time
import schedule
from string import punctuation
import nltk
from nltk.corpus import stopwords

bot = telebot.TeleBot('1725519373:AAEwmtfr4Qr5stY9mV61iqaBtA80j8abLsk')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f'Здравствуйте, {message.from_user.first_name}.'
                          f' Этот бот умеет отправлять новости, полученные с сайта https://www.rbc.ru/story/\n'
                          f'Используйте /help чтобы увидеть весь список доступных команд.')
    update_user_db(message.from_user.id)


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, f'Список всех возможных команд:\n'
                          f'1. /help - получить это сообщение.\n'
                          f'2. /new_docs - показать <N> самых свежих новостей.\n'
                          f'3. /new_topics - показать <N> самых свежих тем.\n'
                          f'4. /get_topics - получить список всех тем в базе.\n'
                          f'5. /get_docs <Номер/Название> - получить список всех новостей в данной теме.\n'
                          f'6. /topic <Номер/Название> - показать заголовки 5 самых свежих новостей в этой теме.\n'
                          f'7. /doc <Номер/Название> - показать текст документа с заданным заголовком.\n'
                          f'8. /describe_doc <Номер/Название> - получить статистику по новости.\n'
                          f'9. /subscribe - Подписаться на ежечасную рассылку новостей.\n'
                          f'10 /unsubscribe - Отписаться от ежечасной рассылки новостей.\n')


@bot.message_handler(commands=['subscribe'])
def command(message):
    flag = subscribe(message.from_user.id)
    if flag:
        bot.reply_to(message, "Вы уже были подписаны.")
    else:
        bot.reply_to(message, "Вы подписались на рассылку.")


@bot.message_handler(commands=['unsubscribe'])
def command(message):
    flag = unsubscribe(message.from_user.id)
    if flag:
        bot.reply_to(message, "Вы не были подписаны.")
    else:
        bot.reply_to(message, "Вы отписались от рассылки.")


@bot.message_handler(commands=['get_topics'])
def get_topics(message):
    output_str = ''
    for row in Theme.select():
        flags = "".join(analyse_flags(row.name))
        output_str += f"{row.id}. {flags}{row.name}{flags}\n"
    bot.send_message(message.chat.id, output_str)


@bot.message_handler(commands=['get_docs'])
def command(message):
    bot.send_message(message.chat.id, "Какая тема?")
    bot.register_next_step_handler(message, get_docs)


@bot.message_handler(commands=['new_docs'])
def command(message):
    bot.send_message(message.chat.id, "Сколько новостей?")
    bot.register_next_step_handler(message, new_docs)


@bot.message_handler(commands=['new_topics'])
def command(message):
    bot.send_message(message.chat.id, "Сколько тем?")
    bot.register_next_step_handler(message, new_topics)


@bot.message_handler(commands=['topic'])
def command(message):
    bot.send_message(message.chat.id, "Какая тема?")
    bot.register_next_step_handler(message, topic)


@bot.message_handler(commands=['doc'])
def command(message):
    bot.send_message(message.chat.id, "Какая новость?")
    bot.register_next_step_handler(message, doc)


@bot.message_handler(commands=['describe_doc'])
def command(message):
    bot.send_message(message.chat.id, "Какая новость?")
    bot.register_next_step_handler(message, describe_doc)


"""*************************************************************"""


def nltk_convers(text):
    spec_symb = punctuation + '\n\xa0«»\t—…'
    text = "".join([ch for ch in text.lower() if ch not in spec_symb])
    text_tokens = nltk.word_tokenize(text)
    filtered_tokens = []
    stop_words = stopwords.words("russian")
    for token in text_tokens:
        if token not in stop_words:
            filtered_tokens.append(token)
    text = nltk.Text(filtered_tokens)
    fdist = nltk.FreqDist(text)
    return fdist


def analyse_flags(text):
    words = nltk_convers(text)
    topics = {'🇺🇦': ['укр', 'киев', 'зеленск', 'донба', 'донецк', 'луганск'],
              '🇺🇸': ['сша', 'амер', 'вашингт', 'байден'],
              '🇬🇧': ['англи', 'великобритан', 'лондон', 'джонсо', 'brexit'],
              '🇷🇺': ['русс', 'росси', 'москв', 'путин', 'навальн'],
              '🦠': ['пандеми', 'коронав', 'вирус', 'covid', 'карантин', 'вакцин']}
    output = []
    for word in words:
        for topic_ in topics:
            if topic_ in output:
                continue
            for root in topics[topic_]:
                if root in word:
                    output.append(topic_)
                    break
    return output


def new_docs(message):
    if message.text.isdigit():
        number = int(message.text)
        for news in Story.select().order_by(Story.last_upd.desc()).limit(number):
            theme = "".join(analyse_flags(news.text))
            bot.send_message(message.chat.id,
                             f"{theme}{news.name.upper()}{theme}\n\n {news.text}\nИсточник: {news.url}")
    else:
        bot.send_message(message.chat.id, 'Цифру, пожалуйста.')


def new_topics(message):
    if message.text.isdigit():
        number = int(message.text)
        for theme in Theme.select().order_by(Theme.pub_date.desc()).limit(number):
            flags = "".join(analyse_flags(theme.name))
            bot.send_message(message.chat.id,
                             f"{flags}{theme.name.upper()}{flags}\n\n {theme.pub_date}\nИсточник: {theme.url}")
    else:
        bot.send_message(message.chat.id, 'Цифру, пожалуйста.')


def topic(message):
    text = message.text
    if text.isdigit():
        find = Theme.select().where(Theme.id == text)
        if find:
            text = find[0].name
        else:
            bot.send_message(message.chat.id, 'Темы с таким номером в нашей базе нет.')
            return
    if Theme.select().where(Theme.name == text):
        flags = "".join(analyse_flags(text))
        bot.send_message(message.chat.id, f"{flags}{text.upper()}{flags}")
        for news in Story.select().where(Story.theme == text).order_by(Story.last_upd.desc()).limit(5):
            flags = "".join(analyse_flags(news.text))
            bot.send_message(message.chat.id,
                             f"{flags}{news.name.upper()}{flags}\n\n {news.last_upd}\nИсточник: {news.url}")
    else:
        bot.send_message(message.chat.id, 'Темы с таким названием в нашей базе нет.')


def doc(message):
    text = message.text
    if text.isdigit():
        find = Story.select().where(Story.id == text)
        if find:
            text = find[0].name
        else:
            bot.send_message(message.chat.id, 'Новости с таким номером в нашей базе нет.')
            return
    news = Story.select().where(Story.name == text)
    if news:
        news = news[0]
        flags = "".join(analyse_flags(news.text))
        bot.send_message(message.chat.id,
                         f"{flags}{news.name.upper()}{flags}\n\n {news.text}\nИсточник: {news.url}")
    else:
        bot.send_message(message.chat.id, 'Новости с таким названием в нашей базе нет.')


def describe_doc(message):
    text = message.text
    if text.isdigit():
        find = Story.select().where(Story.id == text)
        if find:
            text = find[0].name
        else:
            bot.send_message(message.chat.id, 'Новости с таким номером в нашей базе нет.')
            return
    news = Story.select().where(Story.name == text)
    if news:
        news = news[0]
        fdist = nltk_convers(news.text)
        output_str = ''
        mean_len = 0
        for word in fdist.most_common(len(fdist)):
            output_str += f"{word[0]} - {word[1]}\n"
            mean_len += len(word[0])
        mean_len = mean_len // len(fdist)
        bot.send_message(message.chat.id, f"Частота употреблений слов:\n{output_str}"
                                          f"\nСредняя длина слов - {mean_len}")
    else:
        bot.send_message(message.chat.id, 'Новости с таким названием в нашей базе нет.')


def get_docs(message):
    text = message.text
    if text.isdigit():
        find = Theme.select().where(Theme.id == text)
        if find:
            text = find[0].name
        else:
            bot.send_message(message.chat.id, 'Темы с таким номером в нашей базе нет.')
            return
    if Theme.select().where(Theme.name == text):
        for news in Story.select().where(Story.theme == text).order_by(Story.id):
            flags = "".join(analyse_flags(news.text))
            bot.send_message(message.chat.id,
                             f"{news.id}. {flags}{news.name}{flags}\n")
    else:
        bot.send_message(message.chat.id, 'Темы с таким названием в нашей базе нет.')


def unsubscribe(user_id):
    users_db.connect()
    user = User.select().where(User.user_id == user_id)
    flag = False
    if not user:
        User.create(user_id=user_id, subscribed=False)
    else:
        if not user[0].subscribed:
            flag = True
        else:
            user[0].subscribed = False
            user[0].save()
    users_db.close()
    return flag


def subscribe(user_id):
    users_db.connect()
    user = User.select().where(User.user_id == user_id)
    flag = False
    if not user:
        User.create(user_id=user_id, subscribed=True)
    else:
        if user[0].subscribed:
            flag = True
        else:
            user[0].subscribed = True
            user[0].save()
    users_db.close()
    return flag


def mailing(last_upd):
    news = Story.select().where(Story.last_upd > last_upd[0]).order_by(Story.last_upd.desc())
    for user in User.select().where(User.subscribed):
        for new_story in news:
            theme = "".join(analyse_flags(new_story.text))
            bot.send_message(user.user_id,
                             f"{theme}{new_story.name.upper()}{theme}\n\n {new_story.text}\nИсточник: {new_story.url}")
    if news:
        last_upd[0] = news[0].last_upd


def threaded_func(func, *args):
    thread = threading.Thread(target=func, args=args)
    thread.start()
    thread.join()


mail_last_upd = [Story.select().order_by(Story.last_upd.desc()).limit(1)[0].last_upd]
bot_thread = threading.Thread(target=bot.polling)
bot_thread.start()
schedule.every().hour.do(threaded_func, update_db)
schedule.every().hour.do(threaded_func, mailing, mail_last_upd)
if __name__ == '__main__':
    while True:
        schedule.run_pending()
        time.sleep(1)
