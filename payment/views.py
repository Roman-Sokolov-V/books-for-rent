import stripe
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, permissions
from rest_framework.decorators import api_view

# from books_rent_config import settings
from payment.permissions import IsAdminOrOwner

from payment.models import Payment
from payment.serialisers import PaymentSerializer
from payment.utils import complete_payment

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all()
        else:
            return Payment.objects.filter(borrowing__user=self.request.user)


class PaymentDetailView(generics.RetrieveAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = (IsAdminOrOwner,)


def payment_success(request):
    return render(request, "payment/success.html")


def payment_cancel(request):
    return render(request, "payment/cancel.html")


endpoint_secret = settings.STRIPE_WEBHOOK_SECRET


@api_view(["POST"])
@csrf_exempt
def my_webhook_view(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        print("⚠️  Webhook signature verification failed." + str(e))
        return HttpResponse(status=400)

    if (
        event["type"] == "checkout.session.completed"
        or event["type"] == "checkout.session.async_payment_succeeded"
    ):
        complete_payment(session_id=event["data"]["object"]["id"])

    return HttpResponse(status=200)
