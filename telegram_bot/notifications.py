from datetime import datetime

import telebot

from books_rent_config.settings import TELEGRAM_BOT_TOKEN

from borrowing.models import Borrowing


def send_created(user_id: int, borrowing: Borrowing) -> None:
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    rented_days = (datetime.today().date() - borrowing.borrow_date).days
    bot.send_message(user_id, f"You rented a {borrowing.book.title} on {borrowing.borrow_date}, the cost of rental is $ {borrowing.book.daily_fee} a day, today accrued the cost of rolling {borrowing.book.daily_fee * rented_days} dollar")
