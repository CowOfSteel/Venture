from rest_framework import viewsets, permissions
from .models import Character
from .serializers import CharacterSerializer

class CharacterViewSet(viewsets.ModelViewSet):
    queryset = Character.objects.all()
    serializer_class = CharacterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Force the owner to be the logged-in user
        serializer.save(user=self.request.user)

    def get_queryset(self):
        # Only return characters that belong to the current user
        return super().get_queryset().filter(user=self.request.user)
from django.shortcuts import render

# Create your views here.
