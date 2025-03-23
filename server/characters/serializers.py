from rest_framework import serializers
from .models import Character, CharacterSkill, Skill, Background


class CharacterSkillSerializer(serializers.ModelSerializer):
    effective_modifier = serializers.IntegerField(source='effective_modifier', read_only=True)

    class Meta:
        model = CharacterSkill
        fields = ['skill', 'level', 'effective_modifier']


class CharacterSerializer(serializers.ModelSerializer):
    # Here we include the character’s skills (via the join table).
    skills = CharacterSkillSerializer(source='characterskill_set', many=True, read_only=True)

    class Meta:
        model = Character
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'

class BackgroundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Background
        fields = '__all__'