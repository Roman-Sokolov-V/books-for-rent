from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

borrowings_keyboard = [
    [
        KeyboardButton(text="show my borrowings"),
        KeyboardButton(text="show my overdue borrowings"),
    ],
]


def get_borrowings_keyboard() -> ReplyKeyboardMarkup:

    keyboard = ReplyKeyboardMarkup(
        keyboard=borrowings_keyboard,
        resize_keyboard=True,
    )
    return keyboard
