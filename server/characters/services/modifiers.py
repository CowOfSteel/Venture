# server/characters/services/modifiers.py

from characters.models import CharacterSkill, Skill


def apply_modifiers(character, modifiers):
    """
    Applies the given modifiers to the character.
    Per your instructions and the SRD:
    - No skill should exceed level-1 during character creation.
    - Attributes should be capped at 18.
    - 'ANY', 'PHYSICAL', or 'MENTAL' attribute bonuses are assigned on the front end,
      so we skip direct changes here unless there's a single specific attribute.
    """

    for mod in modifiers:
        if mod['modifier_type'] == 'ATTRIBUTE':
            category = mod.get('category', '').upper()
            points = mod.get('points', 0)

            # If the category is a generic 'ANY', 'PHYSICAL', or 'MENTAL',
            # we do nothing, because the front end’s bonus_distribution
            # approach handles assigning it to a specific attribute.
            # But if the category is an actual single attribute like 'STRENGTH',
            # we can do something like this:
            #
            # if category == 'STRENGTH':
            #     current_val = character.strength
            #     new_val = min(current_val + points, 18)
            #     character.strength = new_val
            #
            # (And similarly for DEXTERITY, etc.)
            # For now, we'll just skip it unless you implement that logic:
            if category not in ['ANY', 'PHYSICAL', 'MENTAL']:
                # Example: a single specific attribute category
                if category == 'STRENGTH':
                    new_val = min(character.strength + points, 18)
                    character.strength = new_val
                elif category == 'DEXTERITY':
                    new_val = min(character.dexterity + points, 18)
                    character.dexterity = new_val
                # etc. for other attributes if you want
            # Otherwise, do nothing.

        elif mod['modifier_type'] == 'SKILL':
            skill_name = mod.get('skill_name')
            if not skill_name:
                continue  # or raise an error if skill_name is missing

            try:
                skill_obj = Skill.objects.get(name__iexact=skill_name)
            except Skill.DoesNotExist:
                # If the skill doesn't exist, skip or raise an error
                continue

            # The base "points" we’re awarding
            bonus_points = mod.get('points', 0)

            cs = CharacterSkill.objects.filter(character=character, skill=skill_obj).first()
            if cs is None:
                # If we had never picked this skill at all, create a new record.
                # Typically, picking a skill once sets it to level-0, picking it twice sets to level-1,
                # so awarding 1 "point" might be enough to make it level-0 or level-1.
                if bonus_points == 1:
                    # That’s typically level-0 on the first pick
                    initial_level = 0
                else:
                    # if bonus_points >= 2, that might be enough to push it to level-1
                    initial_level = 1
                # But because you never exceed level-1 in creation:
                initial_level = min(initial_level, 1)
                CharacterSkill.objects.create(character=character, skill=skill_obj, level=initial_level)
            else:
                # If we already have the skill at level-0, awarding it again sets it to level-1,
                # but never above 1 at creation time.
                # (If you want to allow level-2 after creation, that’s a separate pipeline.)
                if cs.level == 0 and bonus_points >= 1:
                    cs.level = min(1, cs.level + 1)  # ensure it caps at level-1
                    cs.save()

    character.save()
