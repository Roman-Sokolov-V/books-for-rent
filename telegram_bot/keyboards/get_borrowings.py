from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_borrowings_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="show my borrowings"), KeyboardButton(text="show my overdue borrowings")],
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
    )
    return keyboard