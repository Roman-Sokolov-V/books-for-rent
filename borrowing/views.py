from datetime import date

from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from book.models import Book
from borrowing.models import Borrowing
from borrowing.serializers import BorrowingSerializer, BorrowingBookReturnSerializer, DetailBorrowingSerializer


class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = BorrowingSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Borrowing.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        user_id = self.request.query_params.get("user_id", None)
        is_active = self.request.query_params.get("is_active", None)

        if user_id is not None and self.request.user.is_staff:
            try:
                user = int(user_id)
                queryset = queryset.filter(user_id=user)
            except ValueError:
                return queryset

        if is_active is not None:
            if is_active in {"false", "0", "no"}:
                queryset = queryset.filter(actual_return_date__isnull=False)
            if is_active in {"true", "1", "yes"}:
                queryset = queryset.filter(actual_return_date__isnull=True)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


    def get_serializer_class(self):
        if self.action == "return_book":
            return BorrowingBookReturnSerializer
        if self.action == "retrieve":
            return DetailBorrowingSerializer
        return BorrowingSerializer

    @action(
        detail=True,
        methods=['post'],
        url_path="return"
    )
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        serializer = self.get_serializer(borrowing, data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                borrowing.actual_return_date = date.today()
                borrowing.save()
                book_id = borrowing.book_id
                serializer.save()
                Book.objects.filter(pk=book_id).update(inventory=F("inventory") + 1)
                return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
