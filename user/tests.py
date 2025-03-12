from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

from rest_framework.test import APIClient
from rest_framework.reverse import reverse
from rest_framework import status

User = get_user_model()


class UserManagerTests(TestCase):
    def test_create_user_with_valid_email(self):
        email = "user@example.com"
        password = "testpassword123"
        user = User.objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_email(self):
        with self.assertRaises(ValueError) as context:
            User.objects.create_user(email=None, password="testpassword123")
        self.assertEqual(str(context.exception), "The given email must be set")

    def test_create_superuser_with_valid_email(self):
        email = "admin@example.com"
        password = "adminpassword123"
        superuser = User.objects.create_superuser(
            email=email, password=password
        )

        self.assertEqual(superuser.email, email)
        self.assertTrue(superuser.check_password(password))
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_create_superuser_invalid_is_staff(self):
        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(
                email="admin@example.com", password="password", is_staff=False
            )
        self.assertEqual(
            str(context.exception), "Superuser must have is_staff=True."
        )

    def test_create_superuser_invalid_is_superuser(self):
        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(
                email="admin@example.com",
                password="password",
                is_superuser=False,
            )
        self.assertEqual(
            str(context.exception), "Superuser must have is_superuser=True."
        )


URL_ME = reverse("users:user-me")


class UsersMeAPIEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_unaunthenticated_can_not_retrive(self):
        response = self.client.get(URL_ME)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unaunthenticated_can_not_update(self):
        user_data = {"email": "<EMAIL>", "password": "password"}
        response = self.client.put(URL_ME, data=user_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_aunthenticated_can_retrive_own_data(self):
        user_data = {"email": "<userEMAIL>", "password": "password123"}
        user = get_user_model().objects.create_user(**user_data)
        self.client.force_authenticate(user=user)
        response = self.client.get(URL_ME)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], user.email)
        user_from_db = get_user_model().objects.get(id=user.id)
        self.assertNotEqual(user.password, user_data["password"])
        self.assertTrue(
            check_password(user_data["password"], user_from_db.password)
        )

    def test_aunthenticated_can_update(self):
        user_data = {
            "email": "<userEMAIL>",
            "password": "password123",
        }
        user = get_user_model().objects.create_user(**user_data)
        self.client.force_authenticate(user=user)
        new_user_data = {
            "email": "test@gmail.com",
            "password": "new_password",
        }
        response = self.client.put(URL_ME, data=new_user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], new_user_data["email"])
        user_from_db = get_user_model().objects.get(id=user.id)
        self.assertNotEqual(user.password, new_user_data["password"])
        self.assertTrue(
            check_password(new_user_data["password"], user_from_db.password)
        )


URL_USERS = reverse("users:create-user")


class UsersAPIEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_unaunthenticated_user_can_register(self):
        user_data = {"email": "test@gmail.com", "password": "password"}
        response = self.client.post(URL_USERS, data=user_data)
        user = User.objects.first()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], user.email)
        self.assertEqual(response.data["email"], user_data["email"])
        user_from_db = get_user_model().objects.get(id=user.id)
        self.assertNotEqual(user.password, user_data["password"])
        self.assertTrue(
            check_password(user_data["password"], user_from_db.password)
        )
