from rest_framework import viewsets, permissions
from .models import Character
from .serializers import CharacterSerializer, BackgroundSerializer
from .models import Skill, Background, CharacterSkill
from .serializers import SkillSerializer
from rest_framework import serializers
from rest_framework.response import Response

def apply_background_selection(character, selection):
    """
    Processes the background_selection payload and applies:
      - the chosen background,
      - the free skill,
      - additional skill picks or attribute bonuses from the 'results' list.
    """
    background_id = selection.get('background_id')
    try:
        background = Background.objects.get(id=background_id)
    except Background.DoesNotExist:
        raise serializers.ValidationError("Invalid background_id provided.")
    character.background = background

    # --- Apply the free skill from the background ---
    free_skill_name = background.free_skill
    try:
        skill = Skill.objects.get(name__iexact=free_skill_name)
    except Skill.DoesNotExist:
        raise serializers.ValidationError("The free skill defined in the background does not exist.")
    # Create or upgrade the free skill for the character:
    cs, created = CharacterSkill.objects.get_or_create(character=character, skill=skill, defaults={'level': 0})
    if not created and cs.level < 1:
        cs.level = 1
        cs.save()

    # --- Process additional background results (rolls or manual picks) ---
    # This loop assumes each item in results is a dict with a "type" key.
    results = selection.get('results', [])
    for item in results:
        item_type = item.get('type')
        if item_type == "SKILL":
            skill_name = item.get('name')
            try:
                skill = Skill.objects.get(name__iexact=skill_name)
            except Skill.DoesNotExist:
                continue  # Skip if the skill doesn't exist
            cs, created = CharacterSkill.objects.get_or_create(character=character, skill=skill, defaults={'level': 0})
            if not created and cs.level < 1:
                cs.level = 1
                cs.save()
        elif item_type == "ATTRIBUTE":
            # For now, we’ll simply store attribute bonus details in creation_data.
            # Later, you can expand this to update character attributes directly.
            # Example: {"type": "ATTRIBUTE", "category": "PHYSICAL", "points": 2}
            pass  # TODO: Implement attribute bonus handling

    # --- Save the detailed selection in creation_data for traceability ---
    creation_data = character.creation_data or {}
    creation_data['background_selection'] = selection
    character.creation_data = creation_data
    character.save()

class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated]

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

    def update(self, request, *args, **kwargs):
        # Extract and remove background_selection from request.data if it exists.
        background_selection = request.data.pop('background_selection', None)
        response = super().update(request, *args, **kwargs)
        if background_selection:
            # Apply the background selection to the updated character instance.
            character = self.get_object()
            apply_background_selection(character, background_selection)
        return response

class BackgroundViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Background.objects.all()
    serializer_class = BackgroundSerializer
    permission_classes = [permissions.IsAuthenticated]

