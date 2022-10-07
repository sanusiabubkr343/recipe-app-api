"""
Views for the user API 
"""

import imp

from rest_framework import generics
from rest_framework import viewsets
from user.serializers import loginSerializer, UserSerializer
from django.contrib.auth import get_user_model
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status, filters, viewsets


class UserViewSet(viewsets.ModelViewSet):
    """Create a new user in the system"""

    def get_permissions(self):
        if self.action in ["list", "retrieve", "partial_update"]:
            permission_classes = [IsAuthenticated]

        elif self.action == "destroy":
            permission_classes = [IsAdminUser]

        else:
            permission_classes = [AllowAny]

        return [permission() for permission in permission_classes]

    http_method_names = ["get", "delete", "patch", "post"]
    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()
    permission_classes = [AllowAny]

    @action(
        methods=["POST"],
        detail=False,
        permission_classes=[AllowAny],
        serializer_class=loginSerializer,
        url_path="login-user",
        url_name="login_user",
    )
    def login_user(self, request, *args, **kwargs):
        """User login and get the tokenpair of of access-token and refresh token"""

        def get_tokens_for_user(user):
            refresh = RefreshToken.for_user(user)

            return {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }

        user = (
            get_user_model().objects.all().filter(email=request.data["email"]).first()
        )
        if not user:
            return Response(
                data={"message": "Authentication Failed"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        passwordFlag = user.check_password(request.data["password"])

        if passwordFlag:

            tokens = get_tokens_for_user(user=user)
            serializer = self.serializer_class(instance=user)
            return Response(
                data={"message": "login successful", "token": tokens},
                status=status.HTTP_200_OK,
            )

        return Response(
            data={"message": "Authentication Failed"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
