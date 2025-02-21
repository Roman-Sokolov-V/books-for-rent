from django.core.management.base import BaseCommand
from telegram_bot.bot import start_bot
from telegram_bot.tasks import create_scheduled_task

class Command(BaseCommand):
    help = 'Запускає Telegram бота'

    def handle(self, *args, **options):
        self.stdout.write("Запуск Telegram бота...")
        create_scheduled_task()
        print("scheduled_task starts")
        start_bot()
        print("bot is running")

