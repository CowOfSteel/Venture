from rest_framework import viewsets, permissions
from .models import Character
from .serializers import CharacterSerializer


class CharacterViewSet(viewsets.ModelViewSet):
    queryset = Character.objects.all()
    serializer_class = CharacterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        # If user is staff, return all
        if self.request.user.is_staff:
            return super().get_queryset()
        # Otherwise, limit to just user's own characters
        return super().get_queryset().filter(user=self.request.user)

