from decimal import Decimal
from email.policy import HTTP
import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.conf import settings

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer, TagSerializer


def create_user(email="user@example.com", password="testpass123"):
    """Create and return a new user"""
    return get_user_model().objects.create_user(email, password)


class PublicTagApiTest(TestCase):
    """test unauthenticated API request"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags"""
        url = reverse("recipe:tags-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test authorized API requests"""

    def setUp(self) -> None:
        self.user = create_user()
        self.client = APIClient()

    def user_authenticator(self):
        """Authenticate user 1 of payload"""
        url = reverse("user:users-login_user")
        data = {"email": "user@example.com", "password": "testpass123"}
        settings.USE_TZ = False
        response = self.client.post(url, data, format="json")
        access_token = response.json().get("token").get("access")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + access_token)

    def test_retrieve_tags(self):
        """test getting list of tags"""
        Tag.objects.create(user=self.user, name="vegan")
        Tag.objects.create(user=self.user, name="Dessert")
        Tag.objects.create(user=self.user, name="Spoor")
        Tag.objects.create(user=self.user, name="Geel")
        self.user_authenticator()
        url = reverse("recipe:tags-list")
        res = self.client.get(url, format="json")
        tags = Tag.objects.all().order_by("-name")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json().get("total"), 4)

    def test_create_recipe_with_new_tags(self):
        """Create a recipe with  new tag if not exisiting or leave if exist"""

        payload = {
            "title": "Thai Prawn Curry",
            "time_minutes": 30,
            "price": Decimal("2.50"),
            "tags": [{"name": "Thai"}, {"name": "Dinner"}],
        }
        self.user_authenticator()
        url = reverse("recipe:recipes-list")
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exists = recipe.tags.filter(name=tag["name"], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tag"""
        tag_indian = Tag.objects.create(user=self.user, name="Indian")
        payload = {
            "title": "Pongal",
            "time_minutes": 50,
            "price": Decimal("2.50"),
            "tags": [{"name": "Indian"}, {"name": "Breakfast"}],
        }
        self.user_authenticator()
        url = reverse("recipe:recipes-list")
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())

        for tag in payload["tags"]:
            exists = recipe.tags.filter(name=tag["name"], user=self.user).exists()
            self.assertTrue(exists)
