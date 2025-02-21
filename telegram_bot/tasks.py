from django_q.tasks import schedule
from django_q.models import Schedule
from django.utils import timezone
from datetime import timedelta


# schedule(
#     "telegram_bot.notifications.find_expired_and_send_message",
#     schedule_type='M',
#     next_run=timezone.localtime() + timedelta(minutes=1),
#     repeats=-1,
#)
##  Не забути запускати django-q   python manage.py qcluster

def print_report(*args):
    print(f"schedule {args} created")


def create_scheduled_task():
    Schedule.objects.create(
        func='telegram_bot.notifications.find_expired_and_send_message',
        hook='telegram_bot.tasks.print_report',
        next_run=timezone.localtime().now() + timedelta(seconds=30),
        schedule_type=Schedule.MINUTES,
        repeats=3,
        )
