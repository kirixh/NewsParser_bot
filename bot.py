import telebot
import threading
import time
import schedule
from bot_functions import analyse_flags, describe_doc, doc, \
    get_docs, new_docs, new_topics, topic, subscribe, unsubscribe
from db_config import update_db, update_user_db, Theme, Story, User

bot = telebot.TeleBot('1725519373:AAEwmtfr4Qr5stY9mV61iqaBtA80j8abLsk')


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
    bot.register_next_step_handler(message, get_docs, bot)


@bot.message_handler(commands=['new_docs'])
def bot_new_docs(message):
    bot.send_message(message.chat.id, "Сколько новостей?")
    bot.register_next_step_handler(message, new_docs, bot)


@bot.message_handler(commands=['new_topics'])
def bot_new_topics(message):
    bot.send_message(message.chat.id, "Сколько тем?")
    bot.register_next_step_handler(message, new_topics, bot)


@bot.message_handler(commands=['topic'])
def bot_topic(message):
    bot.send_message(message.chat.id, "Какая тема?")
    bot.register_next_step_handler(message, topic, bot)


@bot.message_handler(commands=['doc'])
def bot_doc(message):
    bot.send_message(message.chat.id, "Какая новость?")
    bot.register_next_step_handler(message, doc, bot)


@bot.message_handler(commands=['describe_doc'])
def bot_describe_doc(message):
    bot.send_message(message.chat.id, "Какая новость?")
    bot.register_next_step_handler(message, describe_doc, bot)


def threaded_func(func, *args):
    """
    Загоняет функцию в поток.
    :param func: функция для исполнения в отдельном потоке
    :param args: аргументы функции
    """
    thread = threading.Thread(target=func, args=args)
    thread.start()  # выполняем функцию
    thread.join()  # закрываем поток


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


mail_last_upd = [Story.select().order_by(Story.last_upd.desc()).limit(1)[0].last_upd]  # время последней новости
bot_thread = threading.Thread(target=bot.polling)  # запускаем бота в отдельном потоке
bot_thread.start()
schedule.every(15).minutes.do(threaded_func, update_db)  # каждые 15 минут обновляется БД сайта в отдельном потоке
# через 5 минут после обновления БД происходит рассылка новостей подписчикам
schedule.every(20).minutes.do(threaded_func, mailing, mail_last_upd)
# Многопоточность используется чтобы не останавливать бота для обновления БД сайта.
if __name__ == '__main__':
    while True:
        schedule.run_pending()
        time.sleep(1)
