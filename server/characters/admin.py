# server/characters/admin.py
from django.contrib import admin
from .models import Background, Skill, Contact

admin.site.register(Background)
admin.site.register(Skill)
admin.site.register(Contact)