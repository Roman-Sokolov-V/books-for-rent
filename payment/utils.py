from decimal import Decimal
import stripe

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from book.models import Book
from borrowing.models import Borrowing
from payment.models import Payment
from payment.serialisers import PaymentSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment(borrowing, amount, type, session_id, session_url, status):
    payload = {
        "borrowing": borrowing,
        "amount": amount,
        "type": type,
        "session_id": session_id,
        "session_url": session_url,
        "status": status,
    }
    serializer = PaymentSerializer(data=payload)
    if serializer.is_valid():
        return serializer.save()
    raise ValidationError(serializer.errors)


def create_stripe_session(
    borrowing: Borrowing, amount: Decimal, payments_type: str
) -> HttpResponseRedirect | None:
    """
    Створює Stripe Payment Session для оплати.
    """
    print("start create session")
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Borrowing {borrowing.id} {borrowing}",
                    },
                    "unit_amount": int(amount * 100),
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url="http://localhost:8000/success/",
        cancel_url="http://localhost:8000/cancel/",
    )
    try:
        create_payment(
            borrowing=borrowing.id,
            amount=amount,
            type=payments_type,
            session_id=session.id,
            session_url=session.url,
            status="PENDING",
        )
        print("Payment created successfully")
        return redirect(session.url, code=303)
    except ValidationError as e:
        print(f"Payment creation failed: {e}")
        return None


def complete_payment(session_id: str):
    payment = Payment.objects.get(session_id=session_id)
    payment.status = "COMPLETED"
    payment.save()
    if payment.type == "FINE":
        with transaction.atomic():
            Borrowing.objects.filter(id=payment.borrowing.id).update(
                actual_return_date=timezone.now().date()
            )
            Book.objects.filter(id=payment.borrowing.book.id).update(
                inventory=F("inventory") + 1
            )
