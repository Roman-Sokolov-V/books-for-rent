from django.core.management.base import BaseCommand
from telegram_bot.bot import start_bot

class Command(BaseCommand):
    help = 'Запускає Telegram бота'

    def handle(self, *args, **options):
        self.stdout.write("Запуск Telegram бота...")
        start_bot()