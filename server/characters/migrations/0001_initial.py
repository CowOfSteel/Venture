# Generated by Django 5.1.7 on 2025-03-21 19:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Character',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('strength', models.IntegerField(default=10)),
                ('dexterity', models.IntegerField(default=10)),
                ('constitution', models.IntegerField(default=10)),
                ('intelligence', models.IntegerField(default=10)),
                ('wisdom', models.IntegerField(default=10)),
                ('charisma', models.IntegerField(default=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='characters', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
