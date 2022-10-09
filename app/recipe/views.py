"""Views for the recipe API"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from core.models import Recipe
from .serializers import RecipeSerializer, RecipeDetailSerializer


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

        return RecipeDetailSerializer

    def perform_create(self, serializer):
        """Create user"""
        serializer.save(user=self.request.user)
