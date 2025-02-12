from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework import generics, permissions

from user.serializers import UserSerializer


class UserCreateAPIView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)


class UserMeView(generics.RetrieveUpdateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.queryset.get(id=self.request.user.id)
