from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField


class Background(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    free_skill = models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)
    version = models.CharField(max_length=20, default="1.0.0")
    growth_table = JSONField(blank=True, null=True)
    learning_table = JSONField(blank=True, null=True)
    manual_table = JSONField(blank=True, null=True)

    def __str__(self):
        return self.name

class Archetype(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    default_modifier = models.IntegerField(default=-1)

    def __str__(self):
        return self.name

class Character(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='characters')
    name = models.CharField(max_length=100)
    goal = models.CharField(max_length=255, blank=True)

    # Basic Attributes
    strength = models.PositiveIntegerField(default=10)
    dexterity = models.PositiveIntegerField(default=10)
    constitution = models.PositiveIntegerField(default=10)
    intelligence = models.PositiveIntegerField(default=10)
    wisdom = models.PositiveIntegerField(default=10)
    charisma = models.PositiveIntegerField(default=10)

    # Flag to determine if character creation is complete.
    is_complete = models.BooleanField(default=False)
    # Field to store in-progress creation data (for returning to the wizard).
    creation_data = JSONField(blank=True, null=True)

    # Relationships with other character-creation components.
    background = models.ForeignKey(Background, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='characters')
    archetypes = models.ManyToManyField(Archetype, blank=True, related_name='characters')
    skills = models.ManyToManyField(Skill, through='CharacterSkill', blank=True, related_name='characters')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def contact_list(self):
        return self.contacts.all()

class CharacterSkill(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    # 'level' represents the invested points.
    # A character with no investment (no record) is treated as -1 by default.
    # When a record exists with level=0, that is considered "Skill: Level-0" (effective modifier 0),
    # level=1 means "Skill: Level-1" (effective modifier +1), etc.
    level = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ('character', 'skill')

    def __str__(self):
        return f"{self.character.name} - {self.skill.name} (Level {self.level})"

    @property
    def effective_modifier(self):
        # If a CharacterSkill record exists, its effective modifier is simply the stored level.
        return self.level

class Modifier(models.Model):
    MODIFIER_TYPE_CHOICES = [
        ('ATTRIBUTE', 'Attribute'),
        ('SKILL', 'Skill'),
    ]
    # Indicates the source of the modifier (e.g., 'Background', 'Edge', 'Focus')
    source = models.CharField(max_length=50)
    # ID of the source record (for traceability)
    source_id = models.IntegerField()
    modifier_type = models.CharField(max_length=20, choices=MODIFIER_TYPE_CHOICES)
    # For ATTRIBUTE type, you can indicate the category (e.g., "PHYSICAL", "MENTAL", or "ANY")
    category = models.CharField(max_length=20, blank=True, null=True)
    # For SKILL type, the specific skill name if applicable (e.g., "Punch", "Shoot")
    skill_name = models.CharField(max_length=50, blank=True, null=True)
    # How many points to add (usually 1 or 2)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.source} (ID: {self.source_id}) - {self.modifier_type}: {self.points}"
class Contact(models.Model):
    RELATIONSHIP_CHOICES = [
        ('acquaintance', 'Acquaintance'),
        ('friend', 'Friend'),
    ]
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100)
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    description = models.TextField(blank=True)  # Optional additional context

    def __str__(self):
        return f"{self.name} ({self.get_relationship_type_display()})"
