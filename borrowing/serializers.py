from django.db import transaction
from django.db.models import F

from datetime import date

from rest_framework import serializers

from book.models import Book
from book.serializers import BookSerializer
from borrowing.models import Borrowing




class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "book", "borrow_date", "expected_return_date", "actual_return_date", "user")
        read_only_fields = ("actual_return_date", "user")

    def validate(self, data):
        Borrowing.validate_dates(
            borrow_date=date.today(),
            expected_return_date=data["expected_return_date"],
            actual_return_date=data.get("actual_return_date"),
            error=serializers.ValidationError
        )
        return data

    def create(self, validated_data):
        book_id = validated_data["book"].id
        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            raise serializers.ValidationError("The selected book does not exist.")

        if book.inventory == 0:
            earliest_return = Borrowing.objects.filter(book=book).order_by("expected_return_date").first()
            if earliest_return:
                raise serializers.ValidationError(f"Sorry this book is not available now, we expect that it book will be available on {earliest_return.expected_return_date}")
            else:
                raise serializers.ValidationError("Sorry this book is not available now.")
            ####################
        # with transaction.atomic():
        #     book.inventory -= 1
        #     book.save()
        #     borrowing = super(BorrowingSerializer, self).create(validated_data)
        # return borrowing
            ##################
        with transaction.atomic():
            Book.objects.filter(pk=book_id).update(inventory=F("inventory") - 1)
            borrowing = super(BorrowingSerializer, self).create(validated_data)
        return borrowing


class BorrowingBookReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("actual_return_date",)


    def validate(self, data):
        if self.instance and self.instance.actual_return_date is not None:
            raise serializers.ValidationError("This book has already been returned.")
        return data

class DetailBorrowingSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    class Meta:
        model = Borrowing
        fields = ("id", "book", "borrow_date", "expected_return_date", "actual_return_date", "user")