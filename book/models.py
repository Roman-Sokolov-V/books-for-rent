from django.db import models


class Book(models.Model):
    class Cover(models.TextChoices):
        HARD = "hard", "Hardcover"
        SOFT = "soft", "Softcover"

    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    cover = models.CharField(max_length=5, choices=Cover)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return f"{self.title} ({self.author})"
