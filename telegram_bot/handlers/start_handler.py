from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from django.utils import timezone

from telegram_bot.keyboards.get_borrowings import get_borrowings_keyboard
from telegram_bot.requests_to_db.account_sync import (
    check_user_sync,
    try_synchronize_accounts,
)
from telegram_bot.requests_to_db.get_borrowings import get_borrowings

router = Router()


class Reg(StatesGroup):
    email = State()
    password = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_exists = await check_user_sync(user_id)
    if user_exists:
        await message.answer(
            f"Hi {message.from_user.first_name}, pick your action",
            reply_markup=get_borrowings_keyboard(),
        )
    else:
        await message.answer(
            f"Hi {message.from_user.first_name}, this is a bot for managing "
            f"books in the library. Please enter your email and Password with "
            f"which you registered in serve are your books to synchronize "
            f"accounts"
        )
        await state.set_state(Reg.email)
        await message.answer("Input email")


@router.message(Reg.email)
async def stage_two(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    await state.set_state(Reg.password)
    await message.answer("Input password")


@router.message(Reg.password)
async def stage_three(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    data = await state.get_data()
    is_valid = await try_synchronize_accounts(
        data, telegram_id=message.from_user.id
    )
    await state.clear()
    if is_valid:
        await message.answer(
            "accounts have synchronize successfully, "
            "please push '/start' again"
        )
    else:
        await message.answer(
            "You input wrong email or/and password, please push '/start' "
            "and try again"
        )


@router.message(F.text.lower() == "show my borrowings")
async def all_borrowings(message: Message):
    borrowings = await get_borrowings(user_id=message.from_user.id)
    for borrowing in borrowings:
        rented_days = (
            borrowing["book__daily_fee"]
            * (timezone.now().date() - borrowing["borrow_date"]).days
        )
        await message.answer(
            f"{borrowing["book__title"]}, is taken {rented_days} "
            f"days ago, daily fee {borrowing['book__daily_fee']}, "
            f"dept for today {borrowing['book__daily_fee'] * rented_days},"
            f" expected return date {borrowing["expected_return_date"]}"
        )


@router.message(F.text.lower() == "show my overdue borrowings")
async def without_puree(message: Message):
    borrowings = await get_borrowings(
        user_id=message.from_user.id, is_overdue=True
    )
    for borrowing in borrowings:
        rented_days = (
            borrowing["book__daily_fee"]
            * (timezone.now().date() - borrowing["borrow_date"]).days
        )
        await message.answer(
            f"{borrowing["book__title"]}, is taken {rented_days} "
            f"days ago, daily fee {borrowing['book__daily_fee']}, "
            f"dept for today {borrowing['book__daily_fee'] * rented_days},"
            f" expected return date {borrowing["expected_return_date"]}"
        )
