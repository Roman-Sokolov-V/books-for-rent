from datetime import date, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.views.generic.dates import timezone_today
from rest_framework.response import Response

from rest_framework.reverse import reverse


from rest_framework.test import APIClient
from rest_framework import status

from book.models import Book
from borrowing.models import Borrowing
from borrowing.serializers import BorrowingSerializer
from borrowing.signals import borrowing_created

URL_BORROWING = reverse("borrowings:borrowings-list")
BOOK_DATA = {
    "title": "Kolobok",
    "author": "unknown",
    "cover": "soft",
    "inventory": 10,
    "daily_fee": 5,
}


def sample_book(**params):
    """Create a sample book."""
    defaults = BOOK_DATA.copy()
    defaults.update(params)
    return Book.objects.create(**defaults)


def sample_bd():
    post_save.disconnect(borrowing_created, sender=Borrowing)
    book = sample_book()
    users = get_user_model().objects.bulk_create(
        [
            get_user_model()(email="user@example.com", password="password"),
            get_user_model()(email="another@example.com", password="another_password"),
            get_user_model()(email="admin@example.com", password="admin_password"),
        ]
    )
    auth_user, another_user, admin = users

    borrows = Borrowing.objects.bulk_create(
        [
            Borrowing(
                expected_return_date=timezone_today() + timedelta(days=1),
                book=book,
                user=auth_user,
            ),
            Borrowing(
                expected_return_date=timezone_today() + timedelta(days=1),
                book=book,
                user=another_user,
            ),
            Borrowing(
                expected_return_date=timezone_today() + timedelta(days=1),
                book=book,
                user=admin,
            ),
        ]
    )

    user_borrow, another_user_borrow, admin_borrow = borrows
    post_save.connect(borrowing_created, sender=Borrowing)
    return (
        book,
        auth_user,
        another_user,
        admin,
        user_borrow,
        another_user_borrow,
        admin_borrow,
    )


class Unauthenticated(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_user_can_not_borrow_books(self):
        response = self.client.post(URL_BORROWING, data=BOOK_DATA)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_can_not_list_borrow_books(self):
        response = self.client.get(URL_BORROWING)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_can_not_return_books(self):
        response = self.client.put(URL_BORROWING + "1/return/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_can_not_retrive_books(self):
        response = self.client.put(URL_BORROWING + "1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class Authenticated(TestCase):
    def setUp(self):
        self.client = APIClient()
        post_save.disconnect(borrowing_created, sender=Borrowing)

    @classmethod
    def tearDownClass(cls):
        post_save.connect(borrowing_created, sender=Borrowing)
        super().tearDownClass()

    def test_authenticated_user_can_list_only_own_borrowings(self):
        (
            book,
            auth_user,
            another_user,
            admin,
            user_borrow,
            another_user_borrow,
            admin_borrow,
        ) = sample_bd()
        self.client.force_authenticate(user=auth_user)
        response = self.client.get(URL_BORROWING)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for borrow in response.data:
            print(borrow["user"])
            self.assertEqual(borrow["user"], auth_user.id)

    def test_filter_is_active(self):
        (
            book,
            auth_user,
            another_user,
            admin,
            auth_user_borrow,
            another_user_borrow,
            admin_borrow,
        ) = sample_bd()
        self.client.force_authenticate(user=auth_user)
        response = self.client.get(URL_BORROWING, {"is_active": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer_is_active = BorrowingSerializer(auth_user_borrow)
        self.assertIn(serializer_is_active.data, response.data)
        response = self.client.get(URL_BORROWING, {"is_active": "false"})
        self.assertNotIn(serializer_is_active.data, response.data)

        actual_return_date = date.today().strftime("%Y-%m-%d")
        auth_user_borrow.actual_return_date = actual_return_date
        auth_user_borrow.save()
        serializer_is_not_active = BorrowingSerializer(auth_user_borrow)
        response = self.client.get(URL_BORROWING, {"is_active": "true"})
        self.assertNotIn(serializer_is_not_active.data, response.data)
        response = self.client.get(URL_BORROWING, {"is_active": "false"})
        self.assertIn(serializer_is_not_active.data, response.data)

    def test_filter_user_id(self):
        """filter shouldn`t working if user is not staff"""
        (
            book,
            auth_user,
            another_user,
            admin,
            auth_user_borrow,
            another_user_borrow,
            admin_borrow,
        ) = sample_bd()
        self.client.force_authenticate(user=auth_user)
        borrowings = Borrowing.objects.filter(user=auth_user)
        serializer = BorrowingSerializer(borrowings, many=True)
        users = {1, 2, 3}
        for user_id in users:
            response = self.client.get(URL_BORROWING, {"user_id": user_id})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, serializer.data)


    @mock.patch("borrowing.views.create_stripe_session")
    def test_authenticated_user_can_create_borrowing(self, mock_session_create):
        mock_session_create.return_value = Response({"session_id": "test_session_123"}, status=200)
        auth_user = get_user_model().objects.create_user(email="<EMAIL>", password="<PASSWORD>")
        book = sample_book()
        self.client.force_authenticate(user=auth_user)
        expected_return_date = timezone_today() + timedelta(days=10)
        expected_return_date_str = expected_return_date.strftime("%Y-%m-%d")
        payload = {
            "expected_return_date": expected_return_date_str,
            "book": book.id,
        }
        self.client.post(URL_BORROWING, data=payload)
        created_borrowing = Borrowing.objects.first()
        self.assertEqual(created_borrowing.user, auth_user)
        self.assertEqual(created_borrowing.book.id, payload["book"])
        self.assertEqual(created_borrowing.borrow_date, date.today())
        self.assertEqual(created_borrowing.expected_return_date, expected_return_date)
        self.assertEqual(created_borrowing.actual_return_date, None)
        amount = (created_borrowing.expected_return_date - created_borrowing.borrow_date).days * book.daily_fee
        mock_session_create.assert_called_once_with(borrowing=created_borrowing, amount=amount, payments_type="PAYMENT")


    def test_should_not_create_with_invalid_data(self):
        book = sample_book()
        user = get_user_model().objects.create_user(
            email="some@email.com", password="somepassword"
        )
        self.client.force_authenticate(user=user)
        expected_return_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        payload = {
            "expected_return_date": expected_return_date,
            "book": book.id,
        }
        response = self.client.post(URL_BORROWING, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        expected_return_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        payload = {
            "expected_return_date": expected_return_date,
            "book": book.id + 1,
        }
        response = self.client.post(URL_BORROWING, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_book_inventory_should_increase_by_1(self):
        # (
        #     book,
        #     auth_user,
        #     another_user,
        #     admin,
        #     user_borrow,
        #     another_user_borrow,
        #     admin_borrow,
        # ) = sample_bd()
        book = sample_book()
        auth_user = get_user_model().objects.create_user(email="<EMAIL>", password="<PASSWORD>")
        book_inventory = book.inventory
        self.client.force_authenticate(user=auth_user)
        expected_return_date = timezone_today() + timedelta(days=10)
        expected_return_date_str = expected_return_date.strftime("%Y-%m-%d")
        payload = {
            "expected_return_date": expected_return_date_str,
            "book": book.id,
        }
        self.client.post(URL_BORROWING, data=payload)
        updated_book = Book.objects.get(id=book.id)
        self.assertEqual(book_inventory - 1, updated_book.inventory)

    def test_borrowing_is_should_not_created_if_book_inventory_is_0(self):
        book = sample_book(inventory=0)
        user = get_user_model().objects.create_user(
            email="some@email.com", password="some_password"
        )
        self.client.force_authenticate(user=user)
        expected_return_date = date.today() + timedelta(days=10)
        expected_return_date_str = expected_return_date.strftime("%Y-%m-%d")
        payload = {
            "expected_return_date": expected_return_date_str,
            "book": book.id,
        }
        response = self.client.post(URL_BORROWING, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        updated_book = Book.objects.get(id=book.id)
        borrowings = Borrowing.objects.all()
        self.assertEqual(updated_book.inventory, 0)
        self.assertEqual(len(borrowings), 0)

    def test_book_can_not_be_returned_twice(self):

        book = sample_book()
        user = get_user_model().objects.create_user(
            email="some@email.com", password="some_password"
        )
        expected_return_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        borrowing = Borrowing.objects.create(
            book=book, user=user, expected_return_date=expected_return_date
        )
        self.client.force_authenticate(user=user)
        response = self.client.post(f"{URL_BORROWING}{borrowing.id}/return/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(f"{URL_BORROWING}{borrowing.id}/return/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        ##Повертає той что брав, чи адмін, дата повернення сьогодні чи обирати
