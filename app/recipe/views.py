"""Views for the recipe API"""

from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from core.models import Recipe, Tag
from .serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
    TagSerializer,
    RecipeImageSerializer,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response


class RecipeViewSets(viewsets.ModelViewSet):
    """view for manage recipe APIs ."""

    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve recipes for authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self):
        if self.action == "list":
            return RecipeSerializer
        if self.action == "upload_image":
            return RecipeImageSerializer

        return RecipeDetailSerializer

    def perform_create(self, serializer):
        """Create user"""
        serializer.save(user=self.request.user)

    @action(
        methods=["POST"], detail=True, url_name="upload_image", url_path="upload-image"
    )
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(viewsets.ModelViewSet):
    """Manage tags in the database"""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Create user"""
        serializer.save(user=self.request.user)
