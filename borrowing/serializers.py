from rest_framework import serializers

from borrowing.models import Borrowing


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "borrow_date", "expected_return_date", "actual_return_date", "user")

    def validate(self, data):
        Borrowing.validate_dates(
            borrowing_date=data["borrow_date"],
            expected_return_date=data["expected_return_date"],
            actual_return_date=data["actual_return_date"],
            error=serializers.ValidationError
        )
        return data