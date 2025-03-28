# server/characters/services/foci.py

from rest_framework import serializers
from characters.models import Focus, CharacterFocus, CharacterSkill, Skill
from characters.services.modifiers import apply_modifiers

def apply_focus_selection(character, focus_selection):
    """
    Applies the chosen focus selection to the given character.
    Expects focus_selection to be a dictionary with a "foci" key containing a list of objects:
      { "id": <focus_id>, "rank": <chosen_rank>, "chosen_skill": <optional> }
    """
    # Clear any existing CharacterFocus entries for this character.
    character.character_focuses.all().delete()

    foci_list = focus_selection.get("foci", [])
    if not foci_list:
        raise serializers.ValidationError("No foci provided in focus_selection.")

    # Initialize a log for any ephemeral focus effects (to be implemented later)
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

        # Validate the chosen rank does not exceed the focus's max_level.
        if rank > focus_obj.max_level:
            raise serializers.ValidationError(
                f"Focus '{focus_obj.name}' cannot be taken at rank {rank} (max level: {focus_obj.max_level})."
            )

        # Create the pivot record in CharacterFocus.
        CharacterFocus.objects.create(
            character=character,
            focus=focus_obj,
            rank=rank,
            chosen_skill=chosen_skill
        )

        # Process immediate effects from the focus's levels.
        levels_data = focus_obj.levels or []
        for level_entry in levels_data:
            if level_entry.get("level", 0) <= rank:
                for effect in level_entry.get("effect_data", []):
                    effect_type = effect.get("type")
                    if effect_type == "GRANT_SKILL":
                        # Retrieve the skill and grant bonus, but cap at level 1 during creation.
                        skill_name = effect.get("skill_name")
                        bonus_points = effect.get("points", 0)
                        try:
                            skill_obj = Skill.objects.get(name__iexact=skill_name)
                        except Skill.DoesNotExist:
                            continue
                        cs = CharacterSkill.objects.filter(character=character, skill=skill_obj).first()
                        if cs is None:
                            level = 1 if bonus_points >= 1 else 0
                            CharacterSkill.objects.create(character=character, skill=skill_obj, level=level)
                        else:
                            if cs.level < 1 and bonus_points >= 1:
                                cs.level = 1
                                cs.save()
                    elif effect_type == "ATTRIBUTE_MOD":
                        # Apply attribute modification and cap at 18.
                        attribute = effect.get("attribute", "").upper()
                        amount = effect.get("amount", 0)
                        if attribute == "STRENGTH":
                            character.vitals.strength = min(character.vitals.strength + amount, 18)
                        elif attribute == "DEXTERITY":
                            character.vitals.dexterity = min(character.vitals.dexterity + amount, 18)
                        elif attribute == "CONSTITUTION":
                            character.vitals.constitution = min(character.vitals.constitution + amount, 18)
                        elif attribute == "INTELLIGENCE":
                            character.vitals.intelligence = min(character.vitals.intelligence + amount, 18)
                        elif attribute == "WISDOM":
                            character.vitals.wisdom = min(character.vitals.wisdom + amount, 18)
                        elif attribute == "CHARISMA":
                            character.vitals.charisma = min(character.vitals.charisma + amount, 18)
                    else:
                        # For unimplemented or ephemeral effects, log them for future processing.
                        focus_ephemeral.append(effect)
    creation_data['focus_ephemeral'] = focus_ephemeral
    character.creation_data = creation_data
    character.save()
