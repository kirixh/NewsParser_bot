import telebot
from db_config import db, update_db, Theme, Story
import time
bot = telebot.TeleBot('1725519373:AAEwmtfr4Qr5stY9mV61iqaBtA80j8abLsk')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f'Я бот. Приятно познакомиться, {message.from_user.first_name}')


def new_docs(message):
    if message.text.isdigit():
        number = int(message.text)
        for news in Story.select().order_by(Story.last_upd.desc()).limit(number):
            bot.send_message(message.chat.id, f"**********{news.name}**********\n\n {news.text}\nИсточник: {news.url}")
    else:
        bot.send_message(message.chat.id, 'Цифру, пожалуйста.')


@bot.message_handler(commands=['new_docs'])
def command_new_docs(message):
    bot.send_message(message.chat.id, "Сколько новостей?")
    bot.register_next_step_handler(message, new_docs)


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
