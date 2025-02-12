from django.shortcuts import render
from rest_framework import generics, mixins, permissions

from book.models import Book
from book.serializers import BookSerializer

from book.permissions import IsAdminOrReadOnly

class BookCreateAPIView(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = (IsAdminOrReadOnly,)


class BookUpdateAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = (IsAdminOrReadOnly,)



