from django.shortcuts import render
from rest_framework import generics, mixins, permissions


from book.models import Book
from book.serializers import BookSerializer


class BookCreateAPIView(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookUpdateAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer



