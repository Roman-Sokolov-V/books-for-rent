from django.contrib.auth import get_user_model
from django.db import models

from book.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.OneToOneField(Book, on_delete=models.CASCADE)
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)

    @staticmethod
    def validate_dates(borrowing_date, expected_return_date, actual_return_date, error):
        if borrowing_date > expected_return_date:
            raise error("Borrowing date must be before expected return date")
        if borrowing_date > actual_return_date:
            raise error("Borrowing date must be before actual return date")

    def clean(self):
        Borrowing.validate_dates(
            borrowing_date=self.borrow_date,
            expected_return_date=self.expected_return_date,
            actual_return_date=self.actual_return_date,
            error=ValueError
        )
