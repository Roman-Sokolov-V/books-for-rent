from django_q.models import Schedule
from django_q.tasks import async_task
from django.utils import timezone
from datetime import timedelta

##  Не забути запускати django-q   python manage.py qcluster


def create_scheduled_task():
    Schedule.objects.create(
        func="telegram_bot.tasks.find_expired_and_send_message",
        next_run=timezone.now() + timedelta(seconds=30),
        schedule_type=Schedule.DAILY,
        repeats=-1,
    )


def find_expired_and_send_message() -> None:
    async_task(
        "telegram_bot.notifications.run_messages_expired",
    )
