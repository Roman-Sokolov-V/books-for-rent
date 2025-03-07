from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import CheckConstraint, Q, F
from django.core.exceptions import ValidationError
from django.db.models.constraints import UniqueConstraint

from book.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="borrowings")

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(expected_return_date__gte=F("borrow_date")),
                name="borrowing_date_must_be_before_expected_return_date",
            ),
            CheckConstraint(
                check=Q(actual_return_date__gte=F("borrow_date")),
                name="borrowing_date_must_be_before_actual_return_date",
            ),
            UniqueConstraint(
                fields=["user", "book"],
                condition=Q(actual_return_date__isnull=True),
                name="unique_active_borrowing",
            )
        ]
    def __str__(self):
        return f"{self.book.title} expected return date {self.expected_return_date}"

    @staticmethod
    def validate_dates(borrow_date, expected_return_date, actual_return_date, error):
        if borrow_date > expected_return_date:
            raise error("Borrowing date must be before expected return date")
        if actual_return_date is not None and borrow_date > actual_return_date:
            raise error("Borrowing date must be before actual return date")

    def clean(self):
        Borrowing.validate_dates(
            borrow_date=self.borrow_date,
            expected_return_date=self.expected_return_date,
            actual_return_date=self.actual_return_date,
            error=ValidationError
        )
