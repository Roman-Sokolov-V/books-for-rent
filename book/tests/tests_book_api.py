from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework.reverse import reverse
from rest_framework import status

BOOK_URL = reverse('book:book-list')

class Unauthenticated(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_is_staff_required(self):
        data = {
            "title": "test_title",
            "author": "test_author",
            "cover": "hard",
            "inventory": 10,
            "daily_fee": 2
        }
        response = self.client.post(BOOK_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
