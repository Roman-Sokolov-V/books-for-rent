from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "first_name", "last_name", "password", "is_staff")
        extra_kwargs = {"password": {"write_only": True}}
        read_only_fields = ("id", "is_staff")

    def create(self, validated_data):
        """create and return a new `User` instance, given the validated data."""
        return get_user_model().objects.create_user(**validated_data)
