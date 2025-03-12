from books_rent_config.settings import TELEGRAM_BOT_TOKEN

import asyncio
from aiogram import Bot, Dispatcher
from telegram_bot.handlers import start_handler

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


async def main():
    print("Telegram bot is running...")
    dp.include_router(start_handler.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Telegram bot stopped")
