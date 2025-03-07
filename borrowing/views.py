from django.db import transaction
from django.db.models import F
from django.views.generic.dates import timezone_today
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from rest_framework import viewsets, generics, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from book.models import Book
from borrowing.models import Borrowing
from borrowing.serializers import (
    BorrowingSerializer,
    BorrowingBookReturnSerializer,
    DetailBorrowingSerializer,
)
from payment.models import Payment

from payment.utils import create_stripe_session

FINE_MULTIPLIER = 2

class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Borrowing Create, List, Retrieve viewset"""
    serializer_class = BorrowingSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """filtering by user and is_active"""
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
        """Assigns the current request user to the borrowing instance, saves it, and returns the instance."""
        return serializer.save(user=self.request.user)

    @extend_schema(
        request=BorrowingSerializer,  # Вхідні дані
        responses={
            303: OpenApiResponse(
                description="Redirect to Stripe Checkout session",
                examples=[
                    OpenApiExample(
                        "Redirect to Stripe",
                        value={"url": "https://checkout.stripe.com/pay/cs_test_..."},
                    )
                ],
            ),
        },
        description=(
                "Creates a new borrowing instance and initiates a Stripe Checkout session. "
                "Creates a new payment instance. Returns a redirect URL to the payment page."
        )
    )
    def create(self, request, *args, **kwargs):
        """When create borrowing call create_stripe_session"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        borrowing = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        amount = (borrowing.expected_return_date - borrowing.borrow_date).days * borrowing.book.daily_fee
        return create_stripe_session(borrowing=borrowing, amount=amount, payments_type="PAYMENT")

    def get_serializer_class(self):
        if self.action == "return_book":
            return BorrowingBookReturnSerializer
        if self.action == "retrieve":
            return DetailBorrowingSerializer
        return BorrowingSerializer

    @action(detail=True, methods=["post"], url_path="return")
    def return_book(self, request, pk=None):
        """return book and update book inventory"""
        borrowing = self.get_object()
        serializer = self.get_serializer(borrowing, data=request.data)
        if serializer.is_valid():
            if timezone_today() > borrowing.expected_return_date and Payment.objects.filter(borrowing=borrowing, type="FINE", status="PAID").exists() == False:
                amount = (timezone_today() - borrowing.expected_return_date).days * borrowing.book.daily_fee * FINE_MULTIPLIER
                return create_stripe_session(borrowing=borrowing, amount=amount, payments_type="FINE")

            with transaction.atomic():
                borrowing.actual_return_date = timezone_today()
                borrowing.save()
                book_id = borrowing.book.id
                serializer.save()
                Book.objects.filter(pk=book_id).update(inventory=F("inventory") + 1)
                return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "user_id",
                type=OpenApiTypes.INT,
                description="Filter by user ID (available only for staff users).",
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                "is_active",
                type=OpenApiTypes.STR,
                enum=["true", "1", "yes", "false", "0", "no"],
                description="Filter by active status. Acceptable values: "
                            "`true, 1, yes` (for active), `false, 0, no` (for inactive).",
                location=OpenApiParameter.QUERY,
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of borrowings"""
        return super().list(request, *args, **kwargs)


