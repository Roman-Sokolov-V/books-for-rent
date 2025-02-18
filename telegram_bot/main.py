import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "books_rent_config.settings")
django.setup()



import telebot
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from telebot import types
from books_rent_config.settings import TELEGRAM_BOT_TOKEN

from borrowing.models import Borrowing



bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def check_user(message, email, password):
    try:
        user = get_user_model().objects.get(email=email)
        if user.check_password(password):
            user.telegram_id = message.from_user.id
            user.save()
            bot.send_message(message.chat.id, "Success")
        else:
            bot.send_message(message.chat.id, "User with this email or/and password does not exist")
    except ObjectDoesNotExist:
        bot.send_message(message.chat.id, "User with this email or/and password does not exist")
    bot.register_next_step_handler(message, get_email)

def get_email(message):
    email = message.text  # Отримуємо текстове повідомлення
    bot.send_message(message.chat.id, "Input password:")
    bot.register_next_step_handler(message, get_password, email)


def get_password(message, email):
    password = message.text
    check_user(message, email, password)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    user_id = message.from_user.id
    if get_user_model().objects.filter(telegram_id=user_id).exists():
        btn3 = types.KeyboardButton("/rented")
        markup.row(btn3)
        bot.send_message(
            message.chat.id,
            f"Hi {message.from_user.first_name}, this is a bot for managing books in the library.",
            reply_markup=markup,
        )
    else:
        #bot.send_message(message.chat.id, "Please enter your email and password of the book rental service")
        bot.send_message(message.chat.id, "input email:")
        bot.register_next_step_handler(message, get_email)


@bot.message_handler(commands=["rented"])
def rented(message):
    borrowings = Borrowing.objects.filter(user__telegram_id=message.from_user.id)
    for borrowing in borrowings:
        bot.send_message(message.chat.id, f"{borrowing}")

bot.polling(none_stop=True)