"""Urls mapping for user API"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import UserViewSet


app_name = "user"

router = DefaultRouter()
router.register("", UserViewSet, basename="users")


urlpatterns = [
    path("", include(router.urls)),
    path("token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify", TokenVerifyView.as_view(), name="token_verify"),
]
