import asyncio
from aiogram import Bot

from django.utils import timezone


from books_rent_config.settings import TELEGRAM_BOT_TOKEN
from borrowing.models import Borrowing


bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_created(user_id: int=674340411, borrowing: Borrowing=None) -> None:
    rented_days = (timezone.now().date() - borrowing.borrow_date).days
    await bot.send_message(
        user_id,
        f"You rented a {borrowing.book.title} on {borrowing.borrow_date}, the cost of rental is $ {borrowing.book.daily_fee} a day, today accrued the cost of rolling {borrowing.book.daily_fee * rented_days} $"
    )
    await bot.session.close()

def run_send_created(user_id: int, borrowing: Borrowing) -> None:
    asyncio.run(send_created(user_id, borrowing))


async def message_expired(user_id: int=674340411, book_title: str="test", expired_days: int=1) -> None:
    await bot.send_message(
        user_id,
        f"Your rented book {book_title} is overdue for {expired_days}, please return the book as soon as possible"
    )
    await bot.session.close()
    print("Message (expired book) is sent")


def run_messages_expired() -> None:
    borrowings = Borrowing.objects.filter(expected_return_date__lt=timezone.now()).select_related("user", "book")
    for borrowing in borrowings:
        expired_days = (timezone.now().date() - borrowing.expected_return_date).days
        if borrowing.user.telegram_id:
            user_id = borrowing.user.telegram_id
            asyncio.run(
                (
                    message_expired(
                        user_id=user_id,
                        book_title=borrowing.book.title,
                        expired_days=expired_days
                    )
                )
            )
        else:
            print(f"user {borrowing.user} - {borrowing.user.email}has not had telegram id yet")

