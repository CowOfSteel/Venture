from django.shortcuts import render
from rest_framework import viewsets, permissions, generics
from .serializers import UserSerializer
from django.contrib.auth.models import User


# The registration view:
class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  # Registration is open
