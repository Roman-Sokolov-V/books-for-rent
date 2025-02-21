from django.utils import timezone
import telebot
from django_q.tasks import async_task
import logging

from books_rent_config.settings import TELEGRAM_BOT_TOKEN

from borrowing.models import Borrowing

logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def send_created(user_id: int, borrowing: Borrowing) -> None:
    rented_days = (timezone.now().date() - borrowing.borrow_date).days
    bot.send_message(
        user_id,
        f"You rented a {borrowing.book.title} on {borrowing.borrow_date}, the cost of rental is $ {borrowing.book.daily_fee} a day, today accrued the cost of rolling {borrowing.book.daily_fee * rented_days} $"
    )

def message_expired(user_id: int, book_title: str, expired_days: int) -> None:
    bot.send_message(
        user_id,
        f"Your rented book {book_title} is overdue for {expired_days}, please return the book as soon as possible"
    )
    print("Message (expired book) is sent")

def find_expired_and_send_message() -> None:
    borrowings = Borrowing.objects.filter(expected_return_date__lt=timezone.now()).select_related("user", "book")
    for borrowing in borrowings:
        expired_days = (timezone.now().date() - borrowing.expected_return_date).days
        if borrowing.user.telegram_id:
            user_id = borrowing.user.telegram_id

            async_task(
                "telegram_bot.notifications.message_expired",
                user_id=user_id,
                book_title=borrowing.book.title,
                expired_days=expired_days,
            )
        else:
            logger.warning(f"The user {borrowing.user.id} has an overdue book but does not have telegram_id")

