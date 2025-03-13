from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework.reverse import reverse
from rest_framework import status

from book.models import Book
from book.serializers import BookSerializer

BOOK_URL = reverse("book:book-list")


def sample_book(**params):
    """Create a sample book."""
    defaults = {
        "title": "Kolobok",
        "author": "unknown",
        "cover": "soft",
        "inventory": 10,
        "daily_fee": 5,
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


class Unauthenticated(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.book = sample_book()
        self.valid_data = {
            "title": "test_title",
            "author": "test_author",
            "cover": "hard",
            "inventory": 10,
            "daily_fee": 2,
        }

    def test_unautheticated_user_can_not_create_book(self):
        response = self.client.post(BOOK_URL, data=self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unautheticated_user_can_list_books(self):
        response = self.client.get(BOOK_URL)
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_unautheticated_user_can_not_update_book(self):
        response = self.client.put(BOOK_URL + "1/", data=self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unautheticated_user_can_retrieve_book(self):
        response = self.client.get(BOOK_URL + "1/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class Authenticated(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.book = sample_book()
        self.valid_data = {
            "title": "test_title",
            "author": "test_author",
            "cover": "hard",
            "inventory": 10,
            "daily_fee": 2,
        }
        self.user = get_user_model().objects.create_user(
            email="<EMAIL>", password="<PASSWORD>"
        )
        self.client.force_authenticate(user=self.user)

    def test_authenticated_user_can_not_create_book(self):
        response = self.client.post(BOOK_URL, data=self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_autheticated_user_can_list_books(self):
        response = self.client.get(BOOK_URL)
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_autheticated_user_can_not_update_book(self):
        response = self.client.put(BOOK_URL + "1/", data=self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_autheticated_user_can_retrieve_book(self):
        response = self.client.get(BOOK_URL + "1/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class Is_Staff_user(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_data = {
            "title": "test_title",
            "author": "test_author",
            "cover": "hard",
            "inventory": 10,
            "daily_fee": 2,
        }
        self.user = get_user_model().objects.create_superuser(
            email="<EMAIL>", password="<PASSWORD>"
        )
        self.client.force_authenticate(user=self.user)

    def test_staff_user_create_book(self):
        response = self.client.post(BOOK_URL, data=self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        book = Book.objects.first()
        for key, value in self.valid_data.items():
            self.assertEqual(getattr(book, key), value)
        serializer = BookSerializer(book)
        self.assertEqual(response.data, serializer.data)

    def test_staff_user_can_list_books(self):
        sample_book()
        response = self.client.get(BOOK_URL)
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_staff_user_can_update_book(self):
        sample_book()
        response = self.client.put(BOOK_URL + "1/", data=self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_autheticated_user_can_retrieve_book(self):
        sample_book()
        response = self.client.get(BOOK_URL + "1/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
