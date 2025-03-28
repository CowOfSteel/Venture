# server/characters/admin.py
from django.contrib import admin
from .models import Background, Skill, Contact, AbilityUsage, Edge, Focus

admin.site.register(Background)
admin.site.register(Skill)
admin.site.register(Contact)
admin.site.register(AbilityUsage)
admin.site.register(Focus)
admin.site.register(Edge)