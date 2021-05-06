import telebot
import threading
from db_config import db, update_db, Theme, Story
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


def dock(message):
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


@bot.message_handler(commands=['get_topics'])
def get_topics(message):
    output_str = ''
    for row in Theme.select():
        flags = "".join(analyse_flags(row.name))
        output_str += f"{row.id}. {flags}{row.name}{flags}\n"
    bot.send_message(message.chat.id, output_str)


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


@bot.message_handler(commands=['dock'])
def command(message):
    bot.send_message(message.chat.id, "Какая новость?")
    bot.register_next_step_handler(message, dock)


def threaded_func(func):
    thread = threading.Thread(target=func)
    thread.start()
    thread.join()


bot_thread = threading.Thread(target=bot.polling)
bot_thread.start()
schedule.every().hour.do(threaded_func, update_db)
if __name__ == '__main__':
    while True:
        schedule.run_pending()
        time.sleep(1)
