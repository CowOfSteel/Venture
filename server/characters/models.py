from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField
from django.utils import timezone


FREQUENCY_CHOICES = [
    ('SCENE', 'Per Scene'),
    ('ROUND', 'Per Round'),
    ('DAY', 'Per Day'),
    ('SESSION', 'Per Session'),
]

class AbilityUsage(models.Model):
    character = models.ForeignKey('Character', on_delete=models.CASCADE, related_name='ability_usages')
    ability_identifier = models.CharField(
        max_length=255,
        help_text="Identifier for the ability (e.g. 'Edge: Ghost' or 'Focus: Reroll Sneak')"
    )
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.character.name} - {self.ability_identifier} usage"

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


class Edge(models.Model):
    # Basic identification
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    # Category for filtering (e.g., COMMON, MAGICAL)
    EDGE_CATEGORY_CHOICES = [
        ('COMMON', 'Common'),
        ('MAGICAL', 'Magical'),
    ]
    category = models.CharField(max_length=20, choices=EDGE_CATEGORY_CHOICES, default='COMMON')

    # Whether the edge can be chosen multiple times
    multi_allowed = models.BooleanField(default=False)

    # Prerequisites as a JSON field (e.g., {"no_underdog": true})
    prerequisites = JSONField(blank=True, null=True)

    # The mechanical effects defined as JSON
    effect_data = JSONField(blank=True, null=True)

    # A text field for usage notes (e.g., "Once per scene, ...")
    usage_notes = models.TextField(blank=True)

    # NEW: Source field to indicate where the edge comes from.
    source = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class CharacterEdge(models.Model):
    character = models.ForeignKey('Character', on_delete=models.CASCADE, related_name='character_edges')
    edge = models.ForeignKey(Edge, on_delete=models.CASCADE, related_name='character_edges')
    # Track if an edge is taken more than once (e.g., Focused)
    rank = models.PositiveSmallIntegerField(default=1)
    # For future ephemeral usage tracking (e.g., usage counters)
    usage_data = JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.character.name} - {self.edge.name} (Rank {self.rank})"


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

    # These attributes will be moved to the CharacterVitals model.
    # Comment them out for now to avoid duplication:
    # strength = models.PositiveIntegerField(default=10)
    # dexterity = models.PositiveIntegerField(default=10)
    # constitution = models.PositiveIntegerField(default=10)
    # intelligence = models.PositiveIntegerField(default=10)
    # wisdom = models.PositiveIntegerField(default=10)
    # charisma = models.PositiveIntegerField(default=10)

    # Flag to determine if character creation is complete.
    is_complete = models.BooleanField(default=False)
    # Field to store in-progress creation data (for returning to the wizard).
    creation_data = JSONField(blank=True, null=True)

    # Relationships with other character-creation components.
    background = models.ForeignKey(Background, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='characters')
    edge = models.ManyToManyField(Edge, blank=True, related_name='characters')
    skills = models.ManyToManyField(Skill, through='CharacterSkill', blank=True, related_name='characters')
    focus = models.ManyToManyField("Focus", through="CharacterFocus", blank=True, related_name="characters")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def contact_list(self):
        return self.contacts.all()


class CharacterVitals(models.Model):
    character = models.OneToOneField(Character, on_delete=models.CASCADE, related_name='vitals')

    # Universal Stats
    current_hp = models.PositiveIntegerField(default=0)
    max_hp = models.PositiveIntegerField(default=0)
    attack_bonus_base = models.IntegerField(default=0)
    base_ac = models.IntegerField(default=0)
    save_physical = models.IntegerField(default=0)
    save_evasion = models.IntegerField(default=0)
    save_mental = models.IntegerField(default=0)
    save_luck = models.IntegerField(default=0)
    is_frail = models.BooleanField(default=False)
    is_mortally_wounded = models.BooleanField(default=False)

    # Moved Attributes (for easier modification later)
    strength = models.PositiveIntegerField(default=10)
    dexterity = models.PositiveIntegerField(default=10)
    constitution = models.PositiveIntegerField(default=10)
    intelligence = models.PositiveIntegerField(default=10)
    wisdom = models.PositiveIntegerField(default=10)
    charisma = models.PositiveIntegerField(default=10)

    # CWn-Specific Fields
    system_strain_current = models.IntegerField(default=0)
    system_strain_max = models.IntegerField(default=0)
    trauma_target = models.IntegerField(default=6)
    major_injuries = JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.character.name}'s Vitals"

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
        return self.level


class Modifier(models.Model):
    MODIFIER_TYPE_CHOICES = [
        ('ATTRIBUTE', 'Attribute'),
        ('SKILL', 'Skill'),
    ]
    source = models.CharField(max_length=50)
    source_id = models.IntegerField()
    modifier_type = models.CharField(max_length=20, choices=MODIFIER_TYPE_CHOICES)
    category = models.CharField(max_length=20, blank=True, null=True)
    skill_name = models.CharField(max_length=50, blank=True, null=True)
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
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_relationship_type_display()})"


class Focus(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=20, default="1.0.0")
    category = models.CharField(max_length=20, default="COMMON")
    source = models.CharField(max_length=100, blank=True)
    max_level = models.PositiveSmallIntegerField(default=2)
    multi_allowed = models.BooleanField(default=False)
    prerequisites = JSONField(blank=True, null=True)
    usage_notes = models.TextField(blank=True)
    levels = JSONField(blank=True, null=True)

    def __str__(self):
        return self.name


class CharacterFocus(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='character_focuses')
    focus = models.ForeignKey(Focus, on_delete=models.CASCADE, related_name='character_focuses')
    rank = models.PositiveSmallIntegerField(default=1)
    chosen_skill = models.CharField(max_length=50, blank=True, null=True)
    usage_data = JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.character.name} - {self.focus.name} (Rank {self.rank})"
