import unittest
import asyncio
from datetime import timedelta

from asgiref.sync import sync_to_async
from django.db.models.signals import post_save
from django.test import TestCase
from unittest.mock import AsyncMock, patch, MagicMock, call
from aiogram.fsm.context import FSMContext
from aiogram import Dispatcher, Bot
import os
import django
from django.contrib.auth import get_user_model
from django.views.generic.dates import timezone_today
from book.models import Book
from borrowing.models import Borrowing
from borrowing.signals import borrowing_created
from telegram_bot.notifications import (
    send_created,
    run_send_created,
    message_expired,
    message_no_expired,
    run_messages_expired,
)
from telegram_bot.requests_to_db.get_borrowings import get_borrowings
from user.models import User
from telegram_bot.handlers import start_handler
from telegram_bot.bot import main
from telegram_bot.handlers.start_handler import cmd_start, stage_two, stage_three
from telegram_bot.keyboards.get_borrowings import (
    get_borrowings_keyboard,
    borrowings_keyboard,
)
from telegram_bot.requests_to_db.account_sync import (
    check_user_sync,
    try_synchronize_accounts,
)
from telegram_bot.handlers.start_handler import Reg

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "books_rent_config.settings")
django.setup()


class TestTelegramBot(unittest.IsolatedAsyncioTestCase):
    """
    Tests for Telegram Botte using AIOGRAM.
    """

    async def asyncSetUp(self):
        """
        Setting up the test environment before performing each test.
        """
        self.bot = AsyncMock(spec=Bot)
        self.dp = Dispatcher()
        self.dp.include_router(start_handler.router)  # Підключаємо роутер обробників

    @patch("telegram_bot.bot.Bot", new_callable=AsyncMock)
    @patch("telegram_bot.bot.Dispatcher", new_callable=AsyncMock)
    async def test_main_function(self, MockDispatcher, MockBot):
        """
        Test the Main () function by checking:
        1. Is the method `delete_webhook`.
        2. Is the `Start_polling` method.
        """
        mock_bot = MockBot.return_value
        mock_dp = MockDispatcher.return_value

        async def run_main():
            await main()
            task = asyncio.create_task(run_main())
            await asyncio.sleep(0.1)
            mock_bot.delete_webhook.assert_called_once_with(drop_pending_updates=True)
            mock_dp.start_polling.assert_called_once_with(mock_bot)
            await self.dp.stop_polling()
            task.cancel()

            with self.assertRaises(asyncio.CancelledError):
                await task


class TestStartHandler(unittest.IsolatedAsyncioTestCase):
    """Tests for handlers"""
    async def asyncSetUp(self):
        self.message = MagicMock()
        self.message.from_user.id = 123456
        self.message.from_user.first_name = "John"
        self.message.text = "/start"
        self.message.answer = AsyncMock()
        self.state = AsyncMock(spec=FSMContext)

    @patch("telegram_bot.handlers.start_handler.get_borrowings_keyboard")
    @patch(
        "telegram_bot.handlers.start_handler.check_user_sync", new_callable=AsyncMock
    )
    async def test_user_exists(
        self, mock_check_user_sync, mock_get_borrowings_keyboard
    ):
        """We test when the user is already registered"""
        mock_check_user_sync.return_value = True
        mock_get_borrowings_keyboard.return_value = "keyboard_mock"

        await cmd_start(self.message, self.state)

        self.message.answer.assert_called_once_with(
            f"Hi John, pick your action", reply_markup="keyboard_mock"
        )
        self.state.set_state.assert_not_called()

    @patch(
        "telegram_bot.handlers.start_handler.check_user_sync", new_callable=AsyncMock
    )
    async def test_user_not_exists(self, mock_check_user_sync):
        """We test when the user is not registered"""
        mock_check_user_sync.return_value = False

        await cmd_start(self.message, self.state)

        self.message.answer.assert_any_call(
            f"Hi John, this is a bot for managing books in the library. Please enter your email and Password"
            f" with which you registered in serve are your books to synchronize accounts"
        )
        self.message.answer.assert_any_call("Input email")
        self.state.set_state.assert_called_once_with(Reg.email)

    async def test_stage_two(self):
        """We test Email input"""
        self.message.text = "test@test.com"

        await stage_two(self.message, self.state)

        self.state.update_data.assert_called_once_with(email="test@test.com")
        self.state.set_state.assert_called_once_with(Reg.password)
        self.message.answer.assert_called_once_with("Input password")

    @patch(
        "telegram_bot.handlers.start_handler.try_synchronize_accounts",
        new_callable=AsyncMock,
    )
    async def test_stage_three_success(self, mock_try_synchronize_accounts):
        """We test successful synchronization of account"""
        self.message.text = "password123"
        self.state.get_data.return_value = {"email": "test@test.com"}
        mock_try_synchronize_accounts.return_value = True

        await stage_three(self.message, self.state)

        self.state.update_data.assert_called_once_with(password="password123")
        self.state.clear.assert_called_once()
        self.message.answer.assert_called_once_with(
            "accounts have synchronize successfully, please push '/start' again"
        )

    @patch(
        "telegram_bot.handlers.start_handler.try_synchronize_accounts",
        new_callable=AsyncMock,
    )
    async def test_stage_three_fail(self, mock_try_synchronize_accounts):
        """Test unsuccessful synchronization of the account"""
        self.message.text = "wrong_password"
        self.state.get_data.return_value = {"email": "test@test.com"}
        mock_try_synchronize_accounts.return_value = False

        await stage_three(self.message, self.state)

        self.state.update_data.assert_called_once_with(password="wrong_password")
        self.state.clear.assert_called_once()
        self.message.answer.assert_called_once_with(
            "You input wrong email or/and password, please push '/start' and try again"
        )


class TestKeyboards(unittest.TestCase):
    """Tests for Keyboards functions."""
    @patch("telegram_bot.keyboards.get_borrowings.ReplyKeyboardMarkup")
    def test_get_borrowings_keyboard(self, mock_reply_keyboard):
        get_borrowings_keyboard()
        mock_reply_keyboard.assert_called_once_with(
            keyboard=borrowings_keyboard,
            resize_keyboard=True,
        )


class TestAccountSync(TestCase):
    """Tests account synchronisation"""
    def setUp(self):
        self.user_1 = get_user_model().objects.create_user(
            email="<EMAIL>", password="<PASSWORD>", telegram_id=1234
        )
        self.correct_data = {"email": "<CORRECT>", "password": "<CORRECT>"}
        self.incorrect_data_1 = {"email": "<CORRECT>", "password": "<INCORRECT>"}
        self.incorrect_data_2 = {"email": "<INCORRECT>", "password": "<CORRECT>"}
        self.incorrect_data_3 = {"email": "<INCORRECT>", "password": "<INCORRECT>"}

    @staticmethod
    async def get_user_async(user_id: int) -> User:
        return await sync_to_async(get_user_model().objects.get)(id=user_id)

    @staticmethod
    async def create_user_async(data: dict) -> None:
        return await sync_to_async(get_user_model().objects.create_user)(**data)

    @staticmethod
    async def check_telegram_id(telegram_id: int) -> bool:
        return await sync_to_async(
            get_user_model().objects.filter(telegram_id=telegram_id).exists
        )()

    async def test_return_true_if_telegram_id_exist(self):
        """
        Tests if True is returned when a user with the given telegram_id exists in the database.
        """
        result = await check_user_sync(self.user_1.telegram_id)
        self.assertTrue(result)

    async def test_return_false_if_not_exist(self):
        """
        Tests if False is returned when a user with the given telegram_id does not exist in the database.
        """
        result = await check_user_sync(self.user_1.telegram_id + 100)
        self.assertFalse(result)

    async def test_add_telegram_id_and_return_true_if_email_and_password_correct(self):
        """
        Tests if telegram_id is correctly added to the user when the email and password are correct,
        and if True is returned after synchronizing accounts.
        """
        user = await self.create_user_async(self.correct_data)
        telegram_id = 12345
        result = await try_synchronize_accounts(
            data=self.correct_data, telegram_id=telegram_id
        )
        self.assertTrue(result)
        user = await self.get_user_async(user_id=user.id)
        self.assertEqual(telegram_id, user.telegram_id)

    async def test_return_false_if_email_and_password_incorrect(self):
        """
        Tests if False is returned when the provided email and/or password are incorrect,
        and ensures that the telegram_id of the user does not change.
        """
        telegram_id = 12345
        result = await try_synchronize_accounts(
            data=self.incorrect_data_1, telegram_id=telegram_id
        )
        self.assertFalse(result)
        result = await try_synchronize_accounts(
            data=self.incorrect_data_2, telegram_id=telegram_id
        )
        self.assertFalse(result)
        result = await try_synchronize_accounts(
            data=self.incorrect_data_3, telegram_id=telegram_id
        )
        self.assertFalse(result)
        self.assertFalse(await self.check_telegram_id(telegram_id))


BOOK_DATA = {
    "title": "Kolobok",
    "author": "unknown",
    "cover": "soft",
    "inventory": 10,
    "daily_fee": 5,
}


def sample_book(**params):
    """Create a sample book."""
    defaults = BOOK_DATA.copy()
    defaults.update(params)
    return Book.objects.create(**defaults)


def sample_bd():
    post_save.disconnect(borrowing_created, sender=Borrowing)
    book_1 = sample_book()
    book_2 = sample_book(title="Kotigoroshko")
    user = get_user_model().objects.create_user(
        email="<EMAIL>", password="<PASSWORD>", telegram_id=11111
    )
    user_2 = get_user_model().objects.create_user(
        email="<EMAIL2>", password="<PASSWORD2>", telegram_id=55555
    )

    borrows = Borrowing.objects.bulk_create(
        [
            Borrowing(
                expected_return_date=timezone_today() + timedelta(days=1),
                book=book_1,
                user=user,
            ),
            Borrowing(
                expected_return_date=timezone_today() + timedelta(days=1),
                book=book_2,
                user=user,
            ),
            Borrowing(
                expected_return_date=timezone_today() + timedelta(days=1),
                book=book_2,
                user=user_2,
            ),
            Borrowing(
                expected_return_date=timezone_today() + timedelta(days=1),
                book=book_1,
                user=user_2,
            ),
        ]
    )
    borrow_user_1, overdue_borrow_user_1, overdue_borrow_user_2, borrow_user_2 = borrows

    overdue_borrow_user_1.borrow_date = timezone_today() - timedelta(days=10)
    overdue_borrow_user_1.expected_return_date = timezone_today() - timedelta(days=2)
    overdue_borrow_user_1.save()

    overdue_borrow_user_2.borrow_date = timezone_today() - timedelta(days=10)
    overdue_borrow_user_2.expected_return_date = timezone_today() - timedelta(days=3)
    overdue_borrow_user_2.save()

    post_save.connect(borrowing_created, sender=Borrowing)
    return (
        user,
        user_2,
        borrow_user_1,
        overdue_borrow_user_1,
        overdue_borrow_user_2,
        borrow_user_2,
        book_1,
        book_2,
    )


class TestGetBorrowings(TestCase):
    """Tests for requests_to_db.get_borrowings"""
    def setUp(self):
        (
            self.user,
            user_2,
            self.not_overdue_borrow,
            self.overdue_borrow,
            another_user_borrow_1,
            borrow_user_2,
            self.book,
            book_2,
        ) = sample_bd()

    @staticmethod
    async def check_is_user(borrowing_list: list, user: User) -> bool:
        for borrowing in borrowing_list:
            if borrowing.user != user:
                return False
        return True

    @staticmethod
    async def check_is_overdue(borrowing_list: list) -> bool:
        for borrowing in borrowing_list:
            if (
                borrowing.actual_return_date is not None
                or borrowing.expected_return_date > timezone_today()
            ):
                return False
        return True

    async def test_list_all_active_borrowings(self):
        """Test that the function returns a list of all active borrowings for the given user."""

        result = await get_borrowings(user_id=self.user.telegram_id, is_overdue=False)
        self.assertIsInstance(result, list)
        self.assertEqual(2, len(result))
        self.assertTrue(self.check_is_user(result, self.user))

    async def test_list_overdue_borrowings(self):
        """Test that the function returns a list of overdue borrowings for the given user."""
        result = await get_borrowings(user_id=self.user.telegram_id, is_overdue=True)
        self.assertIsInstance(result, list)
        self.assertEqual(1, len(result))
        self.assertTrue(self.check_is_user(result, self.user))
        self.assertTrue(self.check_is_overdue(result))


class TestNotifications(TestCase):
    """Tests for notifications"""
    def setUp(self):
        (
            self.user,
            self.user_2,
            self.borrowing,
            self.overdue_borrow,
            self.overdue_borrow_user_2,
            self.borrow_user_2,
            self.book_1,
            self.book_2,
        ) = sample_bd()

    @patch("telegram_bot.notifications.bot.session.close", new_callable=AsyncMock)
    @patch("telegram_bot.notifications.bot.send_message", new_callable=AsyncMock)
    async def test_send_created(self, mock_send_message, mock_close):
        result = await send_created(
            telegram_id=self.user.telegram_id, borrowing=self.borrowing
        )

        expected_message = (
            f"You rented a {self.borrowing.book.title} on {self.borrowing.borrow_date}, "
            f"the cost of rental is $ {self.borrowing.book.daily_fee} a day, "
            f"today accrued the cost of rolling"
            f" {self.borrowing.book.daily_fee * (timezone_today() - self.borrowing.borrow_date).days} $"
        )
        mock_send_message.assert_called_once_with(
            self.user.telegram_id, expected_message
        )
        mock_close.assert_called_once()

    @patch("telegram_bot.notifications.send_created")
    def test_run_send_created(self, mock_send_created):
        telegram_id = 123456
        run_send_created(telegram_id, self.borrowing)
        mock_send_created.assert_called_once_with(telegram_id, self.borrowing)

    @patch("telegram_bot.notifications.bot.session.close", new_callable=AsyncMock)
    @patch("telegram_bot.notifications.bot.send_message", new_callable=AsyncMock)
    async def test_run_messages_expired(self, mock_send_message, mock_close):
        telegram_id = 123456
        expired_days = 3
        await message_expired(
            telegram_id=telegram_id,
            book_title=self.book_1.title,
            expired_days=expired_days,
        )
        expected_message = (
            f"Your rented book {self.book_1.title} is overdue for "
            f"{expired_days} days, please return the book as soon as possible"
        )

        mock_send_message.assert_called_once_with(telegram_id, expected_message)
        mock_close.assert_called_once()

    @patch("telegram_bot.notifications.bot.session.close", new_callable=AsyncMock)
    @patch("telegram_bot.notifications.bot.send_message", new_callable=AsyncMock)
    async def test_message_no_expired(self, mock_send_message, mock_close):
        telegram_id = 123456
        expected_message = "No borrowings overdue today!"
        await message_no_expired(telegram_id=telegram_id)
        mock_send_message.assert_called_once_with(telegram_id, expected_message)
        mock_close.assert_called_once()

    @patch("telegram_bot.notifications.message_no_expired", new_callable=AsyncMock)
    @patch("telegram_bot.notifications.message_expired", new_callable=AsyncMock)
    def test_run_message_expired(self, mock_message_expired, mock_message_no_expired):
        telegram_id = 88888
        get_user_model().objects.create_user(
            email="<EMAIL_3>", password="<PASSWORD>", telegram_id=telegram_id
        )
        expired_days_1 = (
            timezone_today() - self.overdue_borrow.expected_return_date
        ).days
        expired_days_2 = (
            timezone_today() - self.overdue_borrow_user_2.expected_return_date
        ).days
        run_messages_expired()
        mock_message_expired.assert_has_calls(
            [
                call(
                    telegram_id=self.user.telegram_id,
                    book_title=self.book_2.title,
                    expired_days=expired_days_1,
                ),
                call(
                    telegram_id=self.user_2.telegram_id,
                    book_title=self.book_2.title,
                    expired_days=expired_days_2,
                ),
            ],
            any_order=True,
        )
        mock_message_no_expired.assert_has_calls(
            [
                call(telegram_id=telegram_id),
            ],
            any_order=True,
        )
