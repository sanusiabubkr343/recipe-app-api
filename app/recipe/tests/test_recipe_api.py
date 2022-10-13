"""Test for recipe APIS"""
from decimal import Decimal
from email.mime import image
import imp
import os


from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
import tempfile
import os
from PIL import Image


from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer


RECIPES_URL = reverse("recipe:recipes-list")


def image_upload_url(recipe_id):
    """create and return an image upload url"""
    return reverse("recipe:recipes-upload_image", kwargs={"pk": recipe_id})


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

    def test_partial_update(self):
        """Teat partial update of a recipe"""
        original_link = "https://example.com/recipe.pdf"
        self.recipe = create_recipe(
            user=self.user, title="Sample recipe title", link=original_link
        )

        payload = {"title": "New recipe title"}
        url = reverse("recipe:recipes-detail", kwargs={"pk": self.recipe.id})
        self.user_authenticator()
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, payload["title"])
        self.assertEqual(self.recipe.link, original_link)
        self.assertEqual(self.recipe.user, self.user)

    def test_full_update(self):
        """Test full update"""
        self.recipe = create_recipe(
            user=self.user,
            title="Sample recipe title",
            link="https://example.com/recipe.pdf",
            description="sample recipe description",
        )

        payload = {
            "title": "Sample recipe title",
            "link": "https://example.com/recipe.pdf",
            "description": "sample recipe description",
            "time_minutes": 10,
            "price": Decimal("2.33"),
        }
        self.user_authenticator()
        url = reverse("recipe:recipes-detail", kwargs={"pk": self.recipe.id})
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(self.recipe, key), value)

        self.assertEqual(self.recipe.user, self.user)

    def test_delete_recipe(self):
        """Test  deleting a recipe successful"""
        self.recipe = create_recipe(user=self.user)
        self.user_authenticator()
        url = reverse("recipe:recipes-detail", kwargs={"pk": self.recipe.id})
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=self.recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test Trying to delete another users recipe gives error"""
        new_user = get_user_model().objects.create_user(
            email="user2@example.com", password="test123"
        )

        self.recipe = create_recipe(user=new_user)
        url = reverse("recipe:recipes-detail", kwargs={"pk": self.recipe.id})

        self.user_authenticator()
        # user one login but wont get access to delete new_user own

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=self.recipe.id).exists())


class ImageUploadTests(TestCase):
    """Tests for the image upload API"""

    def user_authenticator(self):
        """Authenticate user 1 of payload"""
        url = reverse("user:users-login_user")
        data = {"email": "user@example.com", "password": "testpass123"}
        settings.USE_TZ = False
        response = self.client.post(url, data, format="json")
        access_token = response.json().get("token").get("access")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + access_token)

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@example.com", "testpass123"
        )
        self.user_authenticator()
        self.recipe = create_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            self.user_authenticator()
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.recipe.id)
        payload = {"image": "notanimage"}
        self.user_authenticator()

        res = self.client.post(url, payload, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
