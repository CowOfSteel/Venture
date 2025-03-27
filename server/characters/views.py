from rest_framework import viewsets, permissions, serializers
from rest_framework.response import Response
from .models import Character, Background, Skill, CharacterSkill, Contact, Edge, CharacterEdge, Focus, CharacterFocus
from .serializers import CharacterSerializer,BackgroundSerializer,SkillSerializer, ContactSerializer, EdgeSerializer, FocusSerializer
from .services.modifiers import apply_modifiers
from .services.foci import apply_focus_selection



def apply_focus_selection(character, focus_selection):
    """
    Applies the chosen focus selection to the given character.
    Expects focus_selection to be a dict with a "foci" key containing a list of objects:
      { "id": <focus_id>, "rank": <chosen_rank>, "chosen_skill": <optional> }
    """
    # Clear any existing CharacterFocus entries for this character.
    character.character_focuses.all().delete()

    foci_list = focus_selection.get("foci", [])
    if not foci_list:
        raise serializers.ValidationError("No foci provided in focus_selection.")

    # Initialize a log for any ephemeral focus effects (not fully implemented yet)
    creation_data = character.creation_data or {}
    focus_ephemeral = creation_data.get('focus_ephemeral', [])

    for focus_item in foci_list:
        focus_id = focus_item.get("id")
        rank = focus_item.get("rank", 1)
        chosen_skill = focus_item.get("chosen_skill")  # optional

        try:
            focus_obj = Focus.objects.get(id=focus_id)
        except Focus.DoesNotExist:
            raise serializers.ValidationError(f"Focus with id {focus_id} does not exist.")

        # Validate chosen rank does not exceed max_level.
        if rank > focus_obj.max_level:
            raise serializers.ValidationError(
                f"Focus '{focus_obj.name}' cannot be taken at rank {rank} (max level: {focus_obj.max_level})."
            )

        # Create a pivot record in CharacterFocus.
        CharacterFocus.objects.create(
            character=character,
            focus=focus_obj,
            rank=rank,
            chosen_skill=chosen_skill
        )

        # Process immediate effects from this focus's levels.
        levels_data = focus_obj.levels or []
        for level_entry in levels_data:
            if level_entry.get("level", 0) <= rank:
                for effect in level_entry.get("effect_data", []):
                    effect_type = effect.get("type")
                    if effect_type == "GRANT_SKILL":
                        skill_name = effect.get("skill_name")
                        bonus_points = effect.get("points", 0)
                        # Retrieve the skill object (case-insensitive match)
                        try:
                            skill_obj = Skill.objects.get(name__iexact=skill_name)
                        except Skill.DoesNotExist:
                            # Skip if the skill doesn't exist.
                            continue
                        # Enforce creation rule: maximum skill level is 1.
                        cs = CharacterSkill.objects.filter(character=character, skill=skill_obj).first()
                        if cs is None:
                            # If bonus_points is given and at least 1, set level to 1.
                            level = 1 if bonus_points >= 1 else 0
                            CharacterSkill.objects.create(character=character, skill=skill_obj, level=level)
                        else:
                            # If already exists and below 1, upgrade to level 1 if bonus applies.
                            if cs.level < 1 and bonus_points >= 1:
                                cs.level = 1
                                cs.save()
                        # Optionally, you could log if bonus_points exceed what can be applied.
                    elif effect_type == "ATTRIBUTE_MOD":
                        # Example: Modify a specific attribute if not generic.
                        attribute = effect.get("attribute", "").upper()
                        amount = effect.get("amount", 0)
                        if attribute == "STRENGTH":
                            character.strength = min(character.strength + amount, 18)
                        elif attribute == "DEXTERITY":
                            character.dexterity = min(character.dexterity + amount, 18)
                        elif attribute == "CONSTITUTION":
                            character.constitution = min(character.constitution + amount, 18)
                        elif attribute == "INTELLIGENCE":
                            character.intelligence = min(character.intelligence + amount, 18)
                        elif attribute == "WISDOM":
                            character.wisdom = min(character.wisdom + amount, 18)
                        elif attribute == "CHARISMA":
                            character.charisma = min(character.charisma + amount, 18)
                        # For generic categories (ANY, PHYSICAL, MENTAL) we assume the front end handles them.
                    else:
                        # For EPHEMERAL_POWER, FOCUS_BUDGET, or any unimplemented effects,
                        # simply log the effect data in the character's creation_data.
                        focus_ephemeral.append(effect)
    # Save the ephemeral effects log back to creation_data.
    creation_data['focus_ephemeral'] = focus_ephemeral
    character.creation_data = creation_data

    character.save()

def apply_edge_selection(character, selection):
    """
    Applies the chosen edge selection to the given character.
    Expects 'selection' to be a dictionary with an "edges" key containing a list
    of objects with: { id, rank, any_skill_choice } and an optional used_underdog flag.
    """
    edges_list = selection.get("edges")
    if edges_list is None:
        raise serializers.ValidationError("No edges provided in edge_selection.")

    # Replace any existing character edges
    character.character_edges.all().delete()

    for edge_item in edges_list:
        edge_id = edge_item.get("id")
        rank = edge_item.get("rank", 1)
        any_skill_choice = edge_item.get("any_skill_choice", None)

        try:
            edge_obj = Edge.objects.get(id=edge_id)
        except Edge.DoesNotExist:
            raise serializers.ValidationError(f"Edge with id {edge_id} does not exist.")

        # Create the pivot record for this edge
        CharacterEdge.objects.create(character=character, edge=edge_obj, rank=rank)

        # Process any immediate effects from the edge's effect_data
        if edge_obj.effect_data:
            for effect in edge_obj.effect_data:
                effect_type = effect.get("type")
                if effect_type == "GRANT_SKILL":
                    skill_name = effect.get("skill_name")
                    # For "ANY" or "ANY_COMBAT" choices, use the user's selection
                    if skill_name in ["ANY", "ANY_COMBAT"]:
                        if not any_skill_choice:
                            raise serializers.ValidationError(
                                f"Edge '{edge_obj.name}' requires a specific skill choice."
                            )
                        chosen_skill = any_skill_choice
                    else:
                        chosen_skill = skill_name
                    modifier = {
                        "modifier_type": "SKILL",
                        "skill_name": chosen_skill,
                        "points": effect.get("points", 0)
                    }
                    apply_modifiers(character, [modifier])
                elif effect_type == "MOD_FORMULA":
                    creation_data = character.creation_data or {}
                    creation_data['hp_formula'] = effect.get("value")
                    character.creation_data = creation_data
                elif effect_type == "MOD_TRAUMA_TARGET":
                    creation_data = character.creation_data or {}
                    creation_data.setdefault('trauma_target_mod', 0)
                    creation_data['trauma_target_mod'] += effect.get("amount", 0)
                    character.creation_data = creation_data
                # (Additional effect types can be handled here.)
    # Store the used_underdog flag if provided
    if selection.get("used_underdog"):
        creation_data = character.creation_data or {}
        creation_data['used_underdog'] = True
        character.creation_data = creation_data

    character.save()

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
        # Pop background_selection, edge_selection, and focus_selection from payload if present
        background_selection = request.data.pop('background_selection', None)
        edge_selection = request.data.pop('edge_selection', None)
        focus_selection = request.data.pop('focus_selection', None)

        character = self.get_object()

        # Update the character with other fields (including contacts payload if provided)
        serializer = self.get_serializer(character, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if background_selection:
            try:
                apply_background_selection(character, background_selection)
            except serializers.ValidationError as e:
                return Response({"detail": e.detail}, status=400)
            serializer = self.get_serializer(character)

        if edge_selection:
            try:
                apply_edge_selection(character, edge_selection)
            except serializers.ValidationError as e:
                return Response({"detail": e.detail}, status=400)
            serializer = self.get_serializer(character)

        if focus_selection:
            try:
                apply_focus_selection(character, focus_selection)
            except serializers.ValidationError as e:
                return Response({"detail": e.detail}, status=400)
            serializer = self.get_serializer(character)

        return Response(serializer.data)


class BackgroundViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Background.objects.all()
    serializer_class = BackgroundSerializer
    permission_classes = [permissions.IsAuthenticated]

class EdgeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Edge.objects.all()
    serializer_class = EdgeSerializer
    permission_classes = [permissions.IsAuthenticated]

class FocusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Focus.objects.all()
    serializer_class = FocusSerializer
    permission_classes = [permissions.IsAuthenticated]
