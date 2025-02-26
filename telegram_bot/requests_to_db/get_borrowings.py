from asgiref.sync import sync_to_async

from django.utils import timezone

from borrowing.models import Borrowing


@sync_to_async
def get_borrowings(user_id: int, is_overdue: bool = False) -> list[dict]:
    if is_overdue:
        return list(
            Borrowing.objects.filter(
                user__telegram_id=user_id, expected_return_date__lt=timezone.now()
            )
            .select_related("user", "book")
            .values(
                "book__title", "book__daily_fee", "borrow_date", "expected_return_date"
            )
            .order_by("borrow_date")
        )
    return list(
        Borrowing.objects.filter(user__telegram_id=user_id)
        .select_related("user", "book")
        .values("book__title", "book__daily_fee", "borrow_date", "expected_return_date")
        .order_by("borrow_date")
    )
