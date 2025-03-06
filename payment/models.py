from django.db import models
from books_rent_config.settings import AUTH_USER_MODEL
from borrowing.models import Borrowing


class Payment(models.Model):
    STATUS_CHOICES = [("PENDING", "Pending"), ("PAID", "Paid")]
    TYPE_CHOICES = [("PAYMENT", "Payment"), ("FINE", "Fine")]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="PAYMENT")
    borrowing = models.ForeignKey(
        Borrowing, on_delete=models.CASCADE, related_name="payments"
    )
    session_id = models.CharField(max_length=255, unique=True)
    session_url = models.URLField(max_length=500)
    amount = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self):
        return f"Payment - {self.id}, borrowing - {self.borrowing.id}, book - {self.borrowing.book.title}"
