import nltk
from nltk.corpus import stopwords
from string import punctuation
from db_config import users_db, Theme, Story, User

nltk.download('punkt')
nltk.download('stopwords')


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


def new_docs(message, bot):
    """
    Отправляет message самых свежих статей.
    :param bot: Бот
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


def new_topics(message, bot):
    """
        Отправляет message самых свежих тем.
        :param bot: Бот
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


def topic(message, bot):
    """
    Показывает заголовки 5 самых свежих новостей в этой теме.
    :param bot: Бот
    :param message: Номер или название темы
    """
    text = message.text
    if text.isdigit():  # если ввели номер
        find = Theme.select().where(Theme.id == text)
        if find:
            text = find[0].name
        else:
            output_str = 'Темы с таким номером в нашей базе нет.'
            bot.send_message(message.chat.id, output_str)
            return output_str
    if Theme.select().where(Theme.name == text):
        flags = "".join(analyse_flags(text))  # анализирует название темы
        output_str = f"{flags}{text.upper()}{flags}"
        bot.send_message(message.chat.id, output_str)
        for news in Story.select().where(Story.theme == text).order_by(Story.last_upd.desc()).limit(5):
            flags = "".join(analyse_flags(news.text))  # анализирует текст статьи
            output_str = f"{flags}{news.name.upper()}{flags}\n\n" \
                         f" {news.last_upd}\nИсточник: {news.url}"
            bot.send_message(message.chat.id, output_str)
    else:
        output_str = 'Темы с таким названием в нашей базе нет.'
        bot.send_message(message.chat.id, output_str)
    return output_str


def doc(message, bot):
    """
    Показывает текст документа с заданным заголовком.
    :param bot: Бот
    :param message: Номер или название документа
    """
    text = message.text
    if text.isdigit():  # если ввели номер
        find = Story.select().where(Story.id == text)
        if find:
            text = find[0].name
        else:
            output_str = 'Новости с таким номером в нашей базе нет.'
            bot.send_message(message.chat.id, output_str)
            return output_str
    news = Story.select().where(Story.name == text)
    if news:
        news = news[0]
        flags = "".join(analyse_flags(news.text))  # анализируем текст для установки флагов
        output_str = f"{flags}{news.name.upper()}{flags}\n\n {news.text}\nИсточник: {news.url}"
        bot.send_message(message.chat.id, output_str)
    else:
        output_str = 'Новости с таким названием в нашей базе нет.'
        bot.send_message(message.chat.id, output_str)
    return output_str


def describe_doc(message, bot):
    """
    Вывоит частоту употребления слов и среднюю длину слова в статье.
    :param bot: Бот
    :param message: сообщение от пользователя
    """
    text = message.text
    if text.isdigit():  # если ввели номер статьи
        find = Story.select().where(Story.id == text)
        if find:
            text = find[0].name
        else:
            output_str = 'Новости с таким номером в нашей базе нет.'
            bot.send_message(message.chat.id, output_str)
            return output_str
    news = Story.select().where(Story.name == text)
    output_str = ''
    if news:
        news = news[0]
        fdist = nltk_convers(news.text)  # получаем контейнер частот
        mean_len = 0
        for word in fdist.most_common(len(fdist)):
            output_str += f"{word[0]} - {word[1]}\n"
            mean_len += len(word[0])
        mean_len = mean_len // len(fdist)
        output_str = f"Частота употреблений слов:\n{output_str}\nСредняя длина слов - {mean_len}"
        bot.send_message(message.chat.id, output_str)
    else:
        output_str = 'Новости с таким названием в нашей базе нет.'
        bot.send_message(message.chat.id, output_str)
    return output_str


def get_docs(message, bot):
    """
    Выводит все номера и названия статей в данной теме.
    :param bot: Бот
    :param message: сообщение от пользователя
    """
    text = message.text
    output_str = ''
    if text.isdigit():  # если ввели номер темы
        find = Theme.select().where(Theme.id == text)
        if find:
            text = find[0].name
        else:
            output_str = 'Темы с таким номером в нашей базе нет.'
            bot.send_message(message.chat.id, output_str)
            return
    if Theme.select().where(Theme.name == text):
        for news in Story.select().where(Story.theme == text).order_by(Story.id):
            flags = "".join(analyse_flags(news.text))  # анализируем текст статьи для установки флагов
            output_str = f"{news.id}. {flags}{news.name}{flags}\n"
            bot.send_message(message.chat.id, output_str)
    else:
        output_str = 'Темы с таким названием в нашей базе нет.'
        bot.send_message(message.chat.id, output_str)
    return output_str


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


def mailing(last_upd, bot):
    """
    Отправка свежих новостей пользователям.
    :param bot: Бот
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
