"""Test for recipe APIS"""
from decimal import Decimal


from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.conf import settings

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer


RECIPES_URL = reverse("recipe:recipes-list")


def create_recipe(user, **params):
    """Create and returns a simple recipe"""
    defaults = {
        "title": "Sample recipe  title",
        "time_minutes": 22,
        "price": Decimal("5.25"),
        "description": "Sample Description",
        "link": "http://example.com/recipe.pdf",
    }

    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeAPITests(TestCase):
    """Test unathenticated API request"""

    def setUp(self) -> None:
        self.client = APIClient()
        return super().setUp()

    def test_auth_required(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated API request"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@example.com", "testpass123"
        )

    def user_authenticator(self):
        """Authenticate user 1 of payload"""
        url = reverse("user:users-login_user")
        data = {"email": "user@example.com", "password": "testpass123"}
        settings.USE_TZ = False
        response = self.client.post(url, data, format="json")
        access_token = response.json().get("token").get("access")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + access_token)

    def test_retrieve_recipes(self):
        """Test retreiving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        self.user_authenticator()
        res = self.client.get(RECIPES_URL, format="json")
        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json().get("results"), serializer.data)

    def test_recipe_list_limited_to_user(self):
        """To test that list of all(others) recipes is limited to authenticsted user"""

        other_user = get_user_model().objects.create_user(
            "other@example.com", "password123"
        )

        create_recipe(user=other_user)
        create_recipe(user=self.user)
        self.user_authenticator()
        res = self.client.get(RECIPES_URL, format="json")

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json().get("results"), serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""
        self.recipe = create_recipe(user=self.user)

        url = reverse("recipe:recipes-detail", kwargs={"pk": self.recipe.id})
        self.user_authenticator()
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = RecipeDetailSerializer(self.recipe)
        self.assertEqual(response.json(), serializer.data)

    def test_create_recipe(self):
        payload = {
            "title": "Sample recipe",
            "time_minutes": 33,
            "price": Decimal("5.25"),
        }
        url = reverse("recipe:recipes-list")
        self.user_authenticator()
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.json().get("id"))
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    # todo_ add put,patch and delete test too
