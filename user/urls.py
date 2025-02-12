from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from django.urls import path

from user.views import UserCreateAPIView, UserMeView


app_name = "users"
urlpatterns = [
    path("", UserCreateAPIView.as_view(), name="create-user"),
    path("me/", UserMeView.as_view(), name="user-me"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
