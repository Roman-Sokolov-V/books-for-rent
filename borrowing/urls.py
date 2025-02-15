from django.urls import path, include
from rest_framework.routers import DefaultRouter

from borrowing.views import BorrowingViewSet


app_name = "borrowings"

router = DefaultRouter()
router.register("", BorrowingViewSet, basename='borrowings')

urlpatterns = [
    path("", include(router.urls)),
]