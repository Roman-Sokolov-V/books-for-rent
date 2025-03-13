import asyncio
from aiogram import Bot
from django.contrib.auth import get_user_model

from django.views.generic.dates import timezone_today

from books_rent_config.settings import TELEGRAM_BOT_TOKEN
from borrowing.models import Borrowing


bot = Bot(token=TELEGRAM_BOT_TOKEN)


async def send_created(telegram_id: int, borrowing: Borrowing = None) -> None:
    rented_days = (timezone_today() - borrowing.borrow_date).days
    await bot.send_message(
        telegram_id,
        f"You rented a {borrowing.book.title} on {borrowing.borrow_date},"
        f" the cost of rental is $ {borrowing.book.daily_fee} "
        f"a day, today accrued the cost of rolling "
        f"{borrowing.book.daily_fee * rented_days} $",
    )
    await bot.session.close()


def run_send_created(telegram_id: int, borrowing: Borrowing) -> None:
    asyncio.run(send_created(telegram_id, borrowing))


async def message_expired(
    telegram_id: int, book_title: str, expired_days: int
) -> None:
    await bot.send_message(
        telegram_id,
        f"Your rented book {book_title} is overdue for {expired_days} "
        f"days, please return the book as soon as possible",
    )
    await bot.session.close()
    print("Message (expired book) is sent")


async def message_no_expired(telegram_id: int) -> None:
    await bot.send_message(telegram_id, "No borrowings overdue today!")
    await bot.session.close()


def run_messages_expired() -> None:
    borrowings = Borrowing.objects.filter(
        expected_return_date__lte=timezone_today(),
        actual_return_date__isnull=True,
    ).select_related("user", "book")
    for borrowing in borrowings:
        expired_days = (timezone_today() - borrowing.expected_return_date).days
        if borrowing.user.telegram_id:
            telegram_id = borrowing.user.telegram_id
            asyncio.run(
                (
                    message_expired(
                        telegram_id=telegram_id,
                        book_title=borrowing.book.title,
                        expired_days=expired_days,
                    )
                )
            )
        else:
            print(
                f"user {borrowing.user} - {borrowing.user.email}"
                f"has not had telegram id yet"
            )

    users = (
        get_user_model()
        .objects.prefetch_related("borrowings")
        .exclude(
            telegram_id=None,
            borrowings__expected_return_date__lte=timezone_today(),
        )
        .distinct()
    )
    for user in users:
        if user.telegram_id:
            telegram_id = user.telegram_id
            asyncio.run((message_no_expired(telegram_id=telegram_id)))
