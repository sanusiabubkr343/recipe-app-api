"""
serializer for the user API view
"""

from urllib import request
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
from rest_framework.authtoken.models import Token
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """serializer for the user object"""

    class Meta:
        model = get_user_model()
        fields = ["id", "email", "password", "name"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        """create a user with encrypted password"""

        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update and Return user"""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class loginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, write_only=True)

    class Meta:
        model = get_user_model()
        fields = ["email", "password", "name"]
        read_only_fields = ["name"]
