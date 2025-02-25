from asgiref.sync import sync_to_async

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist


@sync_to_async
def check_user_sync(user_id: int) -> bool:
    return get_user_model().objects.filter(telegram_id=user_id).exists()


@sync_to_async
def try_synchronize_accounts(data: dict, telegram_id: int) -> bool:
    try:
        user = get_user_model().objects.get(email=data["email"])
        if user.check_password(data["password"]):
            user.telegram_id = telegram_id
            user.save()
            return True
        else:
            return False
    except ObjectDoesNotExist:
        return False