import time
from datetime import timedelta
from decimal import Decimal
from unittest import mock
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.http import HttpResponseRedirect
from django.views.generic.dates import timezone_today

from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from book.models import Book
from borrowing.models import Borrowing
from borrowing.signals import borrowing_created
from payment.models import Payment
from payment.serialisers import PaymentSerializer
from payment.utils import (
    create_stripe_session,
    create_payment,
    complete_payment,
)


URL_PAYMENT_LIST = reverse("payments:payments-list")
URL_PAYMENT_FIRST = reverse("payments:payments-detail", kwargs={"pk": 1})
URL_CREATE_BORROWING = reverse("borrowings:borrowings-list")


def make_test_db():
    post_save.disconnect(borrowing_created, sender=Borrowing)
    user = get_user_model().objects.create_user(
        email="<EMAIL>", password="<PASSWORD>"
    )
    admin = get_user_model().objects.create(
        email="<admin_EMAIL>", password="<admin_PASSWORD>", is_staff=True
    )
    book_1 = Book.objects.create(
        title="Test Book",
        author="Test Author",
        cover="hard",
        inventory=10,
        daily_fee=10,
    )
    book_2 = Book.objects.create(
        title="Test Book_2",
        author="Test Author",
        cover="hard",
        inventory=20,
        daily_fee=10,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    expected_return_date = timezone_today() + timedelta(days=1)
    payload = {
        "expected_return_date": expected_return_date.strftime("%Y-%m-%d"),
        "book": book_1.id,
    }
    client.post(URL_CREATE_BORROWING, data=payload)

    client.force_authenticate(user=admin)
    payload["book"] = book_2.id
    client.post(URL_CREATE_BORROWING, data=payload)
    post_save.connect(borrowing_created, sender=Borrowing)
    return user, admin, book_1, book_2


class UnauthenticatedTestCase(APITestCase):
    def setUp(self):
        make_test_db()
        self.client = APIClient()

    def test_should_not_show_payments(self):
        response = self.client.get(URL_PAYMENT_LIST)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.get(URL_PAYMENT_FIRST)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_should_list_only_own_payments(self):
        user, admin, book_1, book_2 = make_test_db()
        self.client.force_authenticate(user=user)
        response = self.client.get(URL_PAYMENT_LIST)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payments = Payment.objects.filter(borrowing__user=user)
        serializer = PaymentSerializer(payments, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_should_retrieve_own_payment(self):
        user, admin, book_1, book_2 = make_test_db()
        self.client.force_authenticate(user=user)
        payment_id = Payment.objects.filter(borrowing__user=user).first().id
        response = self.client.get(
            reverse("payments:payments-detail", kwargs={"pk": payment_id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payments = Payment.objects.get(id=payment_id)
        serializer = PaymentSerializer(payments, many=False)
        self.assertEqual(response.data, serializer.data)

    def test_should_not_retrieve_others_payment(self):
        user, admin, book_1, book_2 = make_test_db()
        self.client.force_authenticate(user=user)
        payment_id = Payment.objects.filter(borrowing__user=admin).first().id
        response = self.client.get(
            reverse("payments:payments-detail", kwargs={"pk": payment_id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminUserTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_should_list_all_payments(self):
        user, admin, book_1, book_2 = make_test_db()
        self.client.force_authenticate(user=admin)
        response = self.client.get(URL_PAYMENT_LIST)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payments = Payment.objects.all()
        serializer = PaymentSerializer(payments, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_should_retrieve_others_payment(self):
        user, admin, book_1, book_2 = make_test_db()
        self.client.force_authenticate(user=admin)
        payment_id = Payment.objects.filter(borrowing__user=user).first().id
        response = self.client.get(
            reverse("payments:payments-detail", kwargs={"pk": payment_id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payments = Payment.objects.get(id=payment_id)
        serializer = PaymentSerializer(payments, many=False)
        self.assertEqual(response.data, serializer.data)


class CreateStripeSession(APITestCase):
    def setUp(self):
        post_save.disconnect(borrowing_created, sender=Borrowing)
        user = get_user_model().objects.create_user(
            email="<EMAIL>", password="<PASSWORD>"
        )
        book_1 = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="hard",
            inventory=10,
            daily_fee=10,
        )
        self.borrowing = Borrowing.objects.create(
            borrow_date=timezone_today(),
            expected_return_date=timezone_today() + timedelta(days=1),
            book=book_1,
            user=user,
        )
        self.amount = Decimal("10.00")
        self.payments_type = "PAYMENT"

    @classmethod
    def tearDownClass(cls):
        post_save.connect(borrowing_created, sender=Borrowing)
        super().tearDownClass()

    @mock.patch("payment.utils.create_payment")
    @mock.patch("payment.utils.stripe.checkout.Session.create")
    def test_should_calling_functions(
        self, mock_create_session, mock_create_payment
    ):
        """
        Test that stripe.checkout.Session.create is called, and create_payment
        is called with correct arguments
        """
        mock_session = MagicMock()
        mock_session.id = "test_session_id"
        mock_session.url = "https://checkout.stripe.com/test_session"
        mock_create_session.return_value = mock_session

        response = create_stripe_session(
            borrowing=self.borrowing,
            amount=self.amount,
            payments_type=self.payments_type,
        )

        mock_create_session.assert_called_once()

        mock_create_payment.assert_called_once_with(
            borrowing=self.borrowing.id,
            amount=self.amount,
            type=self.payments_type,
            session_id=mock_session.id,
            session_url=mock_session.url,
            status="PENDING",
        )
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, mock_session.url)


class CreatePaymentTestCase(APITestCase):
    def setUp(self):
        make_test_db()

    def test_create_payment(self):
        borrowing = Borrowing.objects.first()
        correct_data = {
            "borrowing": borrowing.id,
            "amount": "10.00",
            "type": "PAYMENT",
            "session_id": "test_session_id",
            "session_url": "https://checkout.stripe.com/test_session",
            "status": "PENDING",
        }
        payment = create_payment(**correct_data)
        serializer = PaymentSerializer(payment, many=False)
        serializer_data = serializer.data.copy()
        serializer_data.pop("id", None)
        self.assertDictEqual(correct_data, serializer_data)


class CompletePaymentTestCase(APITestCase):
    def setUp(self):
        make_test_db()
        self.client = APIClient()
        borrowing = Borrowing.objects.first()
        correct_data = {
            "borrowing": borrowing.id,
            "amount": "10.00",
            "type": "PAYMENT",
            "session_id": "test_session_id",
            "session_url": "https://checkout.stripe.com/test_session",
            "status": "PENDING",
        }
        self.payment = create_payment(**correct_data)
        correct_data["type"] = "FINE"
        correct_data["session_id"] = "another_session_id"
        self.fine_payment = create_payment(**correct_data)

    @mock.patch("payment.views.complete_payment")
    @mock.patch("payment.views.stripe.Webhook.construct_event")
    def test_webhook_is_calling(
        self, mock_construct_event, mock_complete_payment
    ):
        """
        Test that stripe.Webhook.construct_event is called, and
        complete_payment is called with correct arguments with correct data
        """
        mock_event = MagicMock()
        mock_event = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": self.payment.session_id}},
        }
        mock_construct_event.return_value = mock_event

        fake_signature = "test_signature"
        fake_payload = b"{}"
        response = self.client.post(
            reverse("payments:payments-webhook"),
            data=fake_payload,
            content_type="application/json",
            **{"HTTP_STRIPE_SIGNATURE": fake_signature},
        )
        mock_construct_event.assert_called_once()
        mock_complete_payment.assert_called_once_with(
            session_id=self.payment.session_id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_payment_completed_correctly(self):
        session_id = self.payment.session_id
        complete_payment(session_id=session_id)
        updated_payment = Payment.objects.get(
            session_id=session_id, id=self.payment.id
        )
        self.assertEqual(updated_payment.status, "COMPLETED")

    def test_if_fine_payment_book_inventory_is_updated(self):
        session_id = self.fine_payment.session_id
        book_inventory_before = self.fine_payment.borrowing.book.inventory
        complete_payment(session_id=session_id)
        updated_payment = Payment.objects.get(
            session_id=session_id, id=self.fine_payment.id
        )
        self.assertEqual(updated_payment.status, "COMPLETED")
        book_inventory_after = updated_payment.borrowing.book.inventory
        self.assertEqual(book_inventory_after, book_inventory_before + 1)
