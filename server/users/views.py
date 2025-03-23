from django.shortcuts import render
from rest_framework import viewsets, permissions, generics
from .serializers import UserSerializer
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_roles(request):
    roles = request.user.groups.values_list('name', flat=True)
    return Response({"roles": roles})

# The registration view:
class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  # Registration is open
