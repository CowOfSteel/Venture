from rest_framework import serializers
from .models import Character, CharacterSkill, Skill, Background, Contact

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'relationship_type', 'description']

class CharacterSkillSerializer(serializers.ModelSerializer):
    effective_modifier = serializers.IntegerField()

    class Meta:
        model = CharacterSkill
        fields = ['skill', 'level', 'effective_modifier']
class CharacterSkillSerializer(serializers.ModelSerializer):
    effective_modifier = serializers.IntegerField

    class Meta:
        model = CharacterSkill
        fields = ['skill', 'level', 'effective_modifier']


class CharacterSerializer(serializers.ModelSerializer):
    skills = CharacterSkillSerializer(source='characterskill_set', many=True, read_only=True)
    # Make contacts writable by removing read_only=True and setting required=False.
    contacts = ContactSerializer(many=True, required=False)

    class Meta:
        model = Character
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        # Pop contacts data if provided in the payload.
        contacts_data = validated_data.pop('contacts', None)

        # Perform the standard update of other fields.
        instance = super().update(instance, validated_data)

        if contacts_data is not None:
            # Enforce the SRD rule:
            # Either exactly 2 contacts of type "acquaintance" OR exactly 1 of type "friend"
            num_acquaintances = sum(1 for c in contacts_data if c.get('relationship_type') == 'acquaintance')
            num_friends = sum(1 for c in contacts_data if c.get('relationship_type') == 'friend')
            if not ((num_acquaintances == 2 and num_friends == 0) or (num_friends == 1 and num_acquaintances == 0)):
                raise serializers.ValidationError(
                    "Contacts must be either exactly two acquaintances or exactly one friend."
                )

            # Remove any existing contacts for this character.
            instance.contacts.all().delete()

            # Create new contacts from the payload.
            for contact_data in contacts_data:
                Contact.objects.create(character=instance, **contact_data)

            # Mark the contacts step as complete in creation_data.
            creation_data = instance.creation_data or {}
            creation_data['contacts_completed'] = True
            instance.creation_data = creation_data

        instance.save()
        return instance

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'

class BackgroundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Background
        fields = '__all__'