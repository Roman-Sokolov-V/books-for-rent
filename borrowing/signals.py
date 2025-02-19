from django.db.models.signals import post_save
from django.dispatch import receiver
from borrowing.models import Borrowing
from telegram_bot.notifications import send_created

@receiver(post_save, sender=Borrowing)
def borrowing_created(sender, instance, created, **kwargs):
    if created:
        print(f"Borrowing '{instance.id}' by {instance.book} has been created.")
        user_id = instance.user.telegram_id
        send_created(user_id, instance)


# @receiver(post_save, sender=Borrowing)
# def paid_success(sender, instance, created, **kwargs):
#     if created:
#         print(f"Borrowing '{instance.id}' by {instance.book} has been created.")
#         user_id = instance.user.telegram_id
#         send_created(user_id, instance)