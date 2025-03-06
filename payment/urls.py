from django.urls import path, include
from rest_framework.routers import DefaultRouter

from payment.views import PaymentListView, PaymentDetailView, my_webhook_view


app_name = "payments"


urlpatterns = [
    path("", PaymentListView.as_view(), name="payments-list"),
    path("<int:pk>/", PaymentDetailView.as_view(), name="payments-detail"),
    path("webhook/", my_webhook_view, name="payments-webhook"),
]
