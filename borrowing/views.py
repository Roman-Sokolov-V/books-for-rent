from datetime import date

from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from book.models import Book
from borrowing.models import Borrowing
from borrowing.serializers import BorrowingSerializer, BorrowingBookReturnSerializer


class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    #queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def get_queryset(self):
        queryset = Borrowing.objects.all()
        user = self.request.query_params.get("user", None)
        is_active = self.request.query_params.get("is_active", None)
        if user is not None:
            try:
                user = int(user)
                queryset = queryset.filter(user_id=user)
            except ValueError:
                return queryset

        if is_active is not None:
            if is_active in {"false", "0", "no"}:
                queryset = queryset.filter(actual_return_date__isnull=False)
            if is_active in {"true", "1", "yes"}:
                queryset = queryset.filter(actual_return_date__isnull=True)
        return queryset

    def get_serializer_class(self):
        if self.action == "return_book":
            return BorrowingBookReturnSerializer
        return BorrowingSerializer

    @action(
        detail=True,
        methods=['post'],
        url_path="return"
    )
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        # borrowing.actual_return_date = date.today()
        # borrowing.save()
        serializer = self.get_serializer(borrowing, data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                book_id = borrowing.book_id
                serializer.save()
                Book.objects.filter(pk=book_id).update(inventory=F("inventory") + 1)
                return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


