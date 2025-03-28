# Generated by Django 5.1.7 on 2025-03-27 00:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0009_focus'),
    ]

    operations = [
        migrations.CreateModel(
            name='CharacterFocus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.PositiveSmallIntegerField(default=1)),
                ('chosen_skill', models.CharField(blank=True, max_length=50, null=True)),
                ('usage_data', models.JSONField(blank=True, null=True)),
                ('character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='character_focuses', to='characters.character')),
                ('focus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='character_focuses', to='characters.focus')),
            ],
        ),
        migrations.AddField(
            model_name='character',
            name='focus',
            field=models.ManyToManyField(blank=True, related_name='characters', through='characters.CharacterFocus', to='characters.focus'),
        ),
    ]
