import telebot
import threading
import time
import schedule
import nltk
from db_config import users_db, User, update_db, update_user_db, Theme, Story
from string import punctuation
from nltk.corpus import stopwords

bot = telebot.TeleBot('TOKEN')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f'Здравствуйте, {message.from_user.first_name}.'
                          f' Этот бот умеет отправлять новости, полученные с сайта https://www.rbc.ru/story/\n'
                          f'Используйте /help чтобы увидеть весь список доступных команд.')
    update_user_db(message.from_user.id)  # обновляем БД пользователей


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, 'Список всех возможных команд:\n'
                          '1. /help - получить это сообщение.\n'
                          '2. /new_docs - показать <N> самых свежих новостей.\n'
                          '3. /new_topics - показать <N> самых свежих тем.\n'
                          '4. /get_topics - получить список всех тем в базе.\n'
                          '5. /get_docs <Номер/Название> - получить список всех новостей в данной теме.\n'
                          '6. /topic <Номер/Название> - показать заголовки 5 самых свежих новостей в этой теме.\n'
                          '7. /doc <Номер/Название> - показать текст документа с заданным заголовком.\n'
                          '8. /describe_doc <Номер/Название> - получить статистику по новости.\n'
                          '9. /subscribe - Подписаться на ежечасную рассылку новостей.\n'
                          '10 /unsubscribe - Отписаться от ежечасной рассылки новостей.\n')


@bot.message_handler(commands=['subscribe'])
def bot_subscribe(message):
    flag = subscribe(message.from_user.id)
    if flag:
        bot.reply_to(message, "Вы уже были подписаны.")
    else:
        bot.reply_to(message, "Вы подписались на рассылку.")


@bot.message_handler(commands=['unsubscribe'])
def bot_unsubscribe(message):
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
def bot_get_docs(message):
    bot.send_message(message.chat.id, "Какая тема?")
    bot.register_next_step_handler(message, get_docs)


@bot.message_handler(commands=['new_docs'])
def bot_new_docs(message):
    bot.send_message(message.chat.id, "Сколько новостей?")
    bot.register_next_step_handler(message, new_docs)


@bot.message_handler(commands=['new_topics'])
def bot_new_topics(message):
    bot.send_message(message.chat.id, "Сколько тем?")
    bot.register_next_step_handler(message, new_topics)


@bot.message_handler(commands=['topic'])
def bot_topic(message):
    bot.send_message(message.chat.id, "Какая тема?")
    bot.register_next_step_handler(message, topic)


@bot.message_handler(commands=['doc'])
def bot_doc(message):
    bot.send_message(message.chat.id, "Какая новость?")
    bot.register_next_step_handler(message, doc)


@bot.message_handler(commands=['describe_doc'])
def bot_describe_doc(message):
    bot.send_message(message.chat.id, "Какая новость?")
    bot.register_next_step_handler(message, describe_doc)


"""*************************************************************"""


def nltk_convers(text):
    """
    Обрабатывает текст, выбрасывая из него стоп-слова и служебные символы
    :param text: текст для обработки
    :return: контейнер (слово - частота)
    """
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
    """
    Анализирует текст, понимая его тематику по корням слов.
    :param text: текст для анализа
    :return: флаги по теме текста, можно добавить в заголовок
    """
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
    """
    Отправляет message самых свежих статей.
    :param message: количество статей.
    """
    if message.text.isdigit():
        number = int(message.text)
        for news in Story.select().order_by(Story.last_upd.desc()).limit(number):
            theme = "".join(analyse_flags(news.text))  # анализируем текст для определения флагов
            bot.send_message(message.chat.id,
                             f"{theme}{news.name.upper()}{theme}\n\n {news.text}\nИсточник: {news.url}")
    else:
        bot.send_message(message.chat.id, 'Цифру, пожалуйста.')


def new_topics(message):
    """
        Отправляет message самых свежих тем.
        :param message: количество тем.
        """
    if message.text.isdigit():
        number = int(message.text)
        for theme in Theme.select().order_by(Theme.pub_date.desc()).limit(number):
            flags = "".join(analyse_flags(theme.name))  # анализируем название темы для определения флагов
            bot.send_message(message.chat.id,
                             f"{flags}{theme.name.upper()}{flags}\n\n {theme.pub_date}\nИсточник: {theme.url}")
    else:
        bot.send_message(message.chat.id, 'Цифру, пожалуйста.')


def topic(message):
    """
    Показывает заголовки 5 самых свежих новостей в этой теме.
    :param message: Номер или название темы
    """
    text = message.text
    if text.isdigit():  # если ввели номер
        find = Theme.select().where(Theme.id == text)
        if find:
            text = find[0].name
        else:
            bot.send_message(message.chat.id, 'Темы с таким номером в нашей базе нет.')
            return
    if Theme.select().where(Theme.name == text):
        flags = "".join(analyse_flags(text))  # анализирует название темы
        bot.send_message(message.chat.id, f"{flags}{text.upper()}{flags}")
        for news in Story.select().where(Story.theme == text).order_by(Story.last_upd.desc()).limit(5):
            flags = "".join(analyse_flags(news.text))  # анализирует текст статьи
            bot.send_message(message.chat.id,
                             f"{flags}{news.name.upper()}{flags}\n\n {news.last_upd}\nИсточник: {news.url}")
    else:
        bot.send_message(message.chat.id, 'Темы с таким названием в нашей базе нет.')


def doc(message):
    """
    Показывает текст документа с заданным заголовком.
    :param message: Номер или название документа
    """
    text = message.text
    if text.isdigit():  # если ввели номер
        find = Story.select().where(Story.id == text)
        if find:
            text = find[0].name
        else:
            bot.send_message(message.chat.id, 'Новости с таким номером в нашей базе нет.')
            return
    news = Story.select().where(Story.name == text)
    if news:
        news = news[0]
        flags = "".join(analyse_flags(news.text))  # анализируем текст для установки флагов
        bot.send_message(message.chat.id,
                         f"{flags}{news.name.upper()}{flags}\n\n {news.text}\nИсточник: {news.url}")
    else:
        bot.send_message(message.chat.id, 'Новости с таким названием в нашей базе нет.')


def describe_doc(message):
    """
    Вывоит частоту употребления слов и среднюю длину слова в статье.
    :param message: сообщение от пользователя
    """
    text = message.text
    if text.isdigit():  # если ввели номер статьи
        find = Story.select().where(Story.id == text)
        if find:
            text = find[0].name
        else:
            bot.send_message(message.chat.id, 'Новости с таким номером в нашей базе нет.')
            return
    news = Story.select().where(Story.name == text)
    if news:
        news = news[0]
        fdist = nltk_convers(news.text)  # получаем контейнер частот
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
    """
    Выводит все номера и названия статей в данной теме.
    :param message: сообщение от пользователя
    """
    text = message.text
    if text.isdigit():  # если ввели номер темы
        find = Theme.select().where(Theme.id == text)
        if find:
            text = find[0].name
        else:
            bot.send_message(message.chat.id, 'Темы с таким номером в нашей базе нет.')
            return
    if Theme.select().where(Theme.name == text):
        for news in Story.select().where(Story.theme == text).order_by(Story.id):
            flags = "".join(analyse_flags(news.text))  # анализируем текст статьи для установки флагов
            bot.send_message(message.chat.id,
                             f"{news.id}. {flags}{news.name}{flags}\n")
    else:
        bot.send_message(message.chat.id, 'Темы с таким названием в нашей базе нет.')


def unsubscribe(user_id):
    """
    Отписаться от ежечасной рассылки.
    :param user_id: id пользователя
    """
    users_db.connect()
    user = User.select().where(User.user_id == user_id)
    flag = False  # флаг, указывающий на законность действий пользователя
    if not user:
        User.create(user_id=user_id, subscribed=False)  # если пользователя не было в БД, добавить
    else:
        if not user[0].subscribed:  # если не был подписан, то это незаконно
            flag = True
        else:
            user[0].subscribed = False  # меняем статус подписки
            user[0].save()
    users_db.close()
    return flag


def subscribe(user_id):
    """
    Подписаться на ежечасную рассылку.
    :param user_id: id пользователя
    """
    users_db.connect()
    user = User.select().where(User.user_id == user_id)
    flag = False  # флаг, указывающий на законность действий пользователя
    if not user:
        User.create(user_id=user_id, subscribed=True)  # если пользователя не было в БД, добавить
    else:
        if user[0].subscribed:  # если был подписан, то это незаконно
            flag = True
        else:
            user[0].subscribed = True  # меняем статус подписки
            user[0].save()
    users_db.close()
    return flag


def mailing(last_upd):
    """
    Отправка свежих новостей пользователям.
    :param last_upd: время последней новости,
     в форме списка из 1 элемента, чтобы можно было изменить внутри функции.
    """
    news = Story.select().where(Story.last_upd > last_upd[0]).order_by(Story.last_upd.desc())
    for user in User.select().where(User.subscribed):  # пробегаем по всем подписчикам
        for new_story in news:  # пробегаем по всем новейшим статьям
            theme = "".join(analyse_flags(new_story.text))  # анализируем текст статьи для установки флагов
            bot.send_message(user.user_id,
                             f"{theme}{new_story.name.upper()}{theme}\n\n {new_story.text}\nИсточник: {new_story.url}")
    if news:
        last_upd[0] = news[0].last_upd


def threaded_func(func, *args):
    """
    Загоняет функцию в поток.
    :param func: функция для исполнения в отдельном потоке
    :param args: аргументы функции
    """
    thread = threading.Thread(target=func, args=args)
    thread.start()  # выполняем функцию
    thread.join()  # закрываем поток


mail_last_upd = [Story.select().order_by(Story.last_upd.desc()).limit(1)[0].last_upd]  # время последней новости
bot_thread = threading.Thread(target=bot.polling)  # запускаем бота в отдельном потоке
bot_thread.start()
schedule.every().hour.do(threaded_func, update_db)  # каждый час обновляется БД сайта в отдельном потоке
# через 5 минут после обновления БД происходит рассылка новостей подписчикам
schedule.every(65).minutes.do(threaded_func, mailing, mail_last_upd)
# Многопоточность используется чтобы не останавливать бота для обновления БД сайта.
if __name__ == '__main__':
    while True:
        schedule.run_pending()
        time.sleep(1)
