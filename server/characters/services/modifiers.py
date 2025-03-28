# server/characters/services/modifiers.py

from rest_framework import serializers
from characters.models import CharacterSkill, Skill

def apply_modifiers(character, modifiers):
    """
    Applies the given modifiers to the character.
    - No skill should exceed level-1 during character creation.
    - Attributes are capped at 18.
    - 'ANY', 'PHYSICAL', or 'MENTAL' attribute bonuses are handled on the front end,
      unless a specific attribute is given.
    """
    for mod in modifiers:
        if mod['modifier_type'] == 'ATTRIBUTE':
            category = mod.get('category', '').upper()
            points = mod.get('points', 0)

            if category not in ['ANY', 'PHYSICAL', 'MENTAL']:
                if category == 'STRENGTH':
                    new_val = min(character.vitals.strength + points, 18)
                    character.vitals.strength = new_val
                elif category == 'DEXTERITY':
                    new_val = min(character.vitals.dexterity + points, 18)
                    character.vitals.dexterity = new_val
                # ... Repeat for other attributes if desired

        elif mod['modifier_type'] == 'SKILL':
            skill_name = mod.get('skill_name')
            if not skill_name:
                continue
            try:
                skill_obj = Skill.objects.get(name__iexact=skill_name)
            except Skill.DoesNotExist:
                continue

            bonus_points = mod.get('points', 0)
            cs = CharacterSkill.objects.filter(character=character, skill=skill_obj).first()

            if cs is None:
                # If awarding 1 point -> level-0, else -> level-1, but never exceed 1
                initial_level = 0 if bonus_points == 1 else 1
                CharacterSkill.objects.create(
                    character=character, skill=skill_obj,
                    level=min(initial_level, 1)
                )
            else:
                # Already have this skill
                if cs.level >= 1 and bonus_points >= 1:
                    # ---------------------------------------------
                    # OPTION 5: Instead of raising an error, skip it:
                    # ---------------------------------------------
                    # Simply ignore awarding more points to a level-1 skill.
                    # If you prefer to throw an error, uncomment:
                    #
                    # raise serializers.ValidationError(
                    #     f"Skill '{skill_obj.name}' is already level-1. Choose another skill."
                    # )
                    #
                    # If skipping, do nothing:
                    continue

                # If skill was level-0, awarding 1+ point sets it to 1
                if cs.level == 0 and bonus_points >= 1:
                    cs.level = 1
                    cs.save()

    character.save()
