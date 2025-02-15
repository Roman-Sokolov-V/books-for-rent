from django.urls import path
from book.views import BookCreateAPIView, BookUpdateAPIView



app_name = 'book'

urlpatterns = [
    path('', BookCreateAPIView.as_view(), name="book-list"),
    path("<int:pk>/", BookUpdateAPIView.as_view(), name="book-detail"),
]