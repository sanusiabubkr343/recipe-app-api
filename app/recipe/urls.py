from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSets, TagViewSet


app_name = "recipe"
router = DefaultRouter()
router.register("tags", TagViewSet, basename="tags")
router.register("", RecipeViewSets, basename="recipes")


urlpatterns = [
    path("", include(router.urls)),
]
