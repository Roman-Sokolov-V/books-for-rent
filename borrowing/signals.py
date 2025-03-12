from django.db.models.signals import post_save
from django.dispatch import receiver
from borrowing.models import Borrowing
from telegram_bot.notifications import run_send_created


@receiver(post_save, sender=Borrowing)
def borrowing_created(sender, instance, created, **kwargs):
    if created:
        telegram_id = instance.user.telegram_id
        run_send_created(telegram_id=telegram_id, borrowing=instance)
        print(
            f"Borrowing '{instance.id}' by {instance.book} has been created."
        )
