# server/characters/admin.py
from django.contrib import admin
from .models import Background, Skill

admin.site.register(Background)
admin.site.register(Skill)