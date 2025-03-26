from rest_framework import serializers
from .models import Character, CharacterSkill, Skill, Background, Contact, Edge, CharacterEdge


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'relationship_type', 'description']


class CharacterSkillSerializer(serializers.ModelSerializer):
    effective_modifier = serializers.IntegerField()

    class Meta:
        model = CharacterSkill
        fields = ['skill', 'level', 'effective_modifier']


class EdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edge
        fields = '__all__'


class CharacterEdgeSerializer(serializers.ModelSerializer):
    # Nest the full edge details for display.
    edge = EdgeSerializer(read_only=True)

    class Meta:
        model = CharacterEdge
        fields = ['edge', 'rank', 'usage_data']


class CharacterSerializer(serializers.ModelSerializer):
    skills = CharacterSkillSerializer(source='characterskill_set', many=True, read_only=True)
    contacts = ContactSerializer(many=True, required=False)
    character_edges = CharacterEdgeSerializer(many=True, read_only=True)

    class Meta:
        model = Character
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        # Pop contacts data if provided in the payload.
        contacts_data = validated_data.pop('contacts', None)
        # Standard update for other fields.
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
