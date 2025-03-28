from rest_framework import serializers
from .models import (
    Character, CharacterSkill, Skill, Background, Contact, Edge,
    CharacterEdge, Focus, CharacterFocus, CharacterVitals, AbilityUsage
)

class FocusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Focus
        fields = '__all__'

class AbilityUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbilityUsage
        fields = [
            'id',
            'character',
            'ability_identifier',
            'frequency',
            'usage_count',
            'last_used',
        ]
        read_only_fields = ['id', 'character', 'last_used']

class CharacterFocusSerializer(serializers.ModelSerializer):
    focus = FocusSerializer(read_only=True)

    class Meta:
        model = CharacterFocus
        fields = ['focus', 'rank', 'chosen_skill', 'usage_data']


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'relationship_type', 'description']

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'description', 'category', 'default_modifier']

class CharacterSkillSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    effective_modifier = serializers.IntegerField()

    class Meta:
        model = CharacterSkill
        fields = ['skill', 'level', 'effective_modifier']


class EdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edge
        fields = '__all__'


class CharacterEdgeSerializer(serializers.ModelSerializer):
    edge = EdgeSerializer(read_only=True)

    class Meta:
        model = CharacterEdge
        fields = ['edge', 'rank', 'usage_data']


class BackgroundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Background
        fields = '__all__'

class CharacterVitalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CharacterVitals
        fields = [
            'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma',
            'current_hp', 'max_hp',
            'attack_bonus_base', 'base_ac',
            'save_physical', 'save_evasion', 'save_mental', 'save_luck',
            'is_frail', 'is_mortally_wounded',
            'system_strain_current', 'system_strain_max',
            'trauma_target', 'major_injuries',
        ]
        # By default, partial updates are allowed if we call patch() with "partial=True"


class CharacterSerializer(serializers.ModelSerializer):
    skills = CharacterSkillSerializer(source='characterskill_set', many=True, read_only=True)
    contacts = ContactSerializer(many=True, required=False)
    character_edges = CharacterEdgeSerializer(many=True, read_only=True)
    character_focuses = CharacterFocusSerializer(many=True, read_only=True)
    # Make vitals writable
    vitals = CharacterVitalsSerializer(required=False)

    class Meta:
        model = Character
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        # Handle nested Vitals
        vitals_data = validated_data.pop('vitals', None)
        if vitals_data is not None:
            # Partial update for nested model
            vitals_serializer = CharacterVitalsSerializer(
                instance=instance.vitals,
                data=vitals_data,
                partial=True
            )
            vitals_serializer.is_valid(raise_exception=True)
            vitals_serializer.save()

        # Handle contacts (unchanged)
        contacts_data = validated_data.pop('contacts', None)
        instance = super().update(instance, validated_data)
        if contacts_data is not None:
            instance.contacts.all().delete()
            for contact_data in contacts_data:
                Contact.objects.create(character=instance, **contact_data)
            creation_data = instance.creation_data or {}
            creation_data['contacts_completed'] = True
            instance.creation_data = creation_data

        instance.save()
        return instance


# Duplicated FocusSerializer (not strictly needed, but left if your code references it)
class FocusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Focus
        fields = '__all__'
