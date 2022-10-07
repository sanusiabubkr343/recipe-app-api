"""
Test for the user API
"""

from ast import Delete
from curses.ascii import CR
import email
from http import client
from urllib import request, response

from webbrowser import get
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase, force_authenticate
from rest_framework import status
from django.conf import settings


CREATE_USER_URL = reverse("user:users-list")


def create_user(**params):
    """Create and return a new user"""

    return get_user_model().objects.create_user(**params)


class AuthenticationTest(APITestCase):
    def setUp(self):

        existing_data = {"email": "active@gmail.com", "password": "password123"}
        create_user(**existing_data)

    def test_login_user(self):
        login_data = {"email": "active@gmail.com", "password": "password123"}

        url = reverse("user:users-login_user")
        response = self.client.post(url, login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PublicUserApiTest(TestCase):
    """tets the public features of the user API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_succes(self):
        """Test  creating a user is successful"""
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name",
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))

        self.assertNotIn("p assword", res.data)

    def test_user_with_email_exists(self):
        """Test error returned if user with email exist"""

        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name",
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class PrivateUserApiTest(APITestCase):
    def setUp(self):

        user_data_1 = {
            "email": "user1@example.com",
            "password": "password123",
            "name": "name1",
        }

        self.user1 = create_user(**user_data_1)
        self.user1_id = self.user1.id

        user_data_2 = {
            "email": "user2@example.com",
            "password": "password123",
            "name": "name2",
        }
        self.user2 = create_user(**user_data_2)
        self.user2_id = self.user2.id

        user_data_3 = {
            "email": "user3@example.com",
            "password": "password123",
            "name": "name3",
        }
        self.user3 = create_user(**user_data_3)
        self.user3_id = self.user3.id

    def user_authenticator(self):
        """Authenticate user 1 of payload"""
        url = reverse("user:users-login_user")
        data = {"email": "user1@example.com", "password": "password123"}
        settings.USE_TZ = False
        response = self.client.post(url, data, format="json")
        access_token = response.json().get("token").get("access")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + access_token)

    def test_user_retrieves(self):
        """get test for user lists"""
        self.user_authenticator()
        url = reverse(
            "user:users-list",
        )
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual((response.json().get("total")), 3)

    def test_user_retrieve(self):

        self.user_authenticator()
        url = reverse("user:users-detail", kwargs={"pk": self.user1_id})
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("email"), "user1@example.com")

    def test_user_update_profile(self):

        data = {"name": "updated name 3", "password": "passwordNew"}
        url = reverse("user:users-detail", kwargs={"pk": self.user3_id})
        self.user_authenticator()
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("name"), data["name"])
        self.assertEqual(response.json().get("email"), "user3@example.com")
        self.assertTrue(
            get_user_model()
            .objects.get(id=self.user3_id)
            .check_password(data["password"])
        )

    def test_deny_a_non_super_user_can_delete(self):
        url = reverse("user:users-detail", kwargs={"pk": self.user2_id})
        self.user_authenticator()
        response = self.client.delete(url, format="json")
        self.assertNotEquals(response.status_code, status.HTTP_204_NO_CONTENT)
