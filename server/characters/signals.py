from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Character, CharacterVitals

@receiver(post_save, sender=Character)
def create_or_update_character_vitals(sender, instance, created, **kwargs):
    if created:
        # Create a CharacterVitals instance with default values.
        # Set current_hp and max_hp to 1 (as a baseline).
        CharacterVitals.objects.create(
            character=instance,
            current_hp=1,
            max_hp=1,
            attack_bonus_base=0,
            base_ac=0,
            save_physical=0,
            save_evasion=0,
            save_mental=0,
            save_luck=0,
            is_frail=False,
            is_mortally_wounded=False,
            strength=10,
            dexterity=10,
            constitution=10,
            intelligence=10,
            wisdom=10,
            charisma=10,
            system_strain_current=0,
            system_strain_max=0,
            trauma_target=6,
            major_injuries=None  # or {} if you prefer an empty dict
        )
    else:
        # Optionally, you can update the vitals here if needed.
        # For now, we simply save the existing vitals to ensure any signals
        # connected with it are triggered.
        if hasattr(instance, 'vitals'):
            instance.vitals.save()
