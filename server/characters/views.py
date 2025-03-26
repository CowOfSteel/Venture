from rest_framework import viewsets, permissions, serializers
from rest_framework.response import Response
from .models import Character, Background, Skill, CharacterSkill, Contact
from .serializers import CharacterSerializer, BackgroundSerializer, SkillSerializer
from .services.modifiers import apply_modifiers

def apply_background_selection(character, selection):
    # Assign the selected background.
    background_id = selection.get('background_id')
    try:
        background = Background.objects.get(id=background_id)
    except Background.DoesNotExist:
        raise serializers.ValidationError("Invalid background_id provided.")
    character.background = background

    # Apply free skill:
    free_skill_name = background.free_skill
    try:
        free_skill = Skill.objects.get(name__iexact=free_skill_name)
    except Skill.DoesNotExist:
        raise serializers.ValidationError("The free skill defined in the background does not exist.")
    free_cs, created = CharacterSkill.objects.get_or_create(
        character=character,
        skill=free_skill,
        defaults={'level': 0}
    )
    if free_cs.level < 1:
        free_cs.level = 1
        free_cs.save()

    # Process additional results (roll-based or manual).
    if selection.get('mode') == 'roll':
        results = selection.get('results', [])
    else:
        results = selection.get('manual_choices', [])

    # Convert each result into a modifier dict.
    modifiers = []
    for item in results:
        if item.get('type') == "ATTRIBUTE":
            modifiers.append({
                'modifier_type': "ATTRIBUTE",
                'category': item.get('category'),
                'points': item.get('points', 0),
            })
        elif item.get('type') == "SKILL":
            modifiers.append({
                'modifier_type': "SKILL",
                'skill_name': item.get('name'),
                'points': item.get('points', 0),
            })
    # Apply the standard modifiers.
    apply_modifiers(character, modifiers)

    # Process bonus distribution if provided.
    bonus_distribution = selection.get('bonus_distribution')
    if bonus_distribution:
        for bonus in bonus_distribution:
            category = bonus.get('category', '').upper()
            assignments = bonus.get('assigned_attributes', {})
            bonus_points = bonus.get('points', 0)
            if sum(assignments.values()) != bonus_points:
                raise serializers.ValidationError("Total bonus assignment does not match bonus points.")
            for attr, pts in assignments.items():
                allowed_attrs = []
                if category == 'ANY':
                    allowed_attrs = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
                elif category == 'PHYSICAL':
                    allowed_attrs = ['strength', 'dexterity', 'constitution']
                elif category == 'MENTAL':
                    allowed_attrs = ['intelligence', 'wisdom', 'charisma']
                if attr not in allowed_attrs:
                    raise serializers.ValidationError(f"Invalid attribute assignment: {attr} for category {category}.")
                current_val = getattr(character, attr)
                if current_val + pts > 18:
                    raise serializers.ValidationError(f"Assignment would exceed attribute cap for {attr}.")
                setattr(character, attr, current_val + pts)

    # Save the creation_data for traceability.
    creation_data = character.creation_data or {}
    creation_data['background_selection'] = selection
    creation_data['background_completed'] = True
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
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        # Pop background_selection from payload if present
        background_selection = request.data.pop('background_selection', None)
        character = self.get_object()

        # Update the character with other fields (including contacts payload if provided)
        serializer = self.get_serializer(character, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # If background_selection was sent, process it.
        if background_selection:
            try:
                apply_background_selection(character, background_selection)
            except serializers.ValidationError as e:
                return Response({"detail": e.detail}, status=400)
            # Reload serializer to reflect changes from background_selection
            serializer = self.get_serializer(character)

        return Response(serializer.data)

class BackgroundViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Background.objects.all()
    serializer_class = BackgroundSerializer
    permission_classes = [permissions.IsAuthenticated]
