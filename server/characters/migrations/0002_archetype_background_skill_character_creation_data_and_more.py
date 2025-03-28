# Generated by Django 5.1.7 on 2025-03-22 22:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Archetype',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Background',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('free_skill', models.CharField(max_length=50)),
                ('is_default', models.BooleanField(default=False)),
                ('version', models.CharField(default='1.0.0', max_length=20)),
                ('growth_table', models.JSONField(blank=True, null=True)),
                ('learning_table', models.JSONField(blank=True, null=True)),
                ('manual_table', models.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('category', models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='character',
            name='creation_data',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='character',
            name='goal',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='character',
            name='is_complete',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='character',
            name='charisma',
            field=models.PositiveIntegerField(default=10),
        ),
        migrations.AlterField(
            model_name='character',
            name='constitution',
            field=models.PositiveIntegerField(default=10),
        ),
        migrations.AlterField(
            model_name='character',
            name='dexterity',
            field=models.PositiveIntegerField(default=10),
        ),
        migrations.AlterField(
            model_name='character',
            name='intelligence',
            field=models.PositiveIntegerField(default=10),
        ),
        migrations.AlterField(
            model_name='character',
            name='strength',
            field=models.PositiveIntegerField(default=10),
        ),
        migrations.AlterField(
            model_name='character',
            name='wisdom',
            field=models.PositiveIntegerField(default=10),
        ),
        migrations.AddField(
            model_name='character',
            name='archetypes',
            field=models.ManyToManyField(blank=True, related_name='characters', to='characters.archetype'),
        ),
        migrations.AddField(
            model_name='character',
            name='background',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='characters', to='characters.background'),
        ),
        migrations.CreateModel(
            name='CharacterSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.PositiveSmallIntegerField(default=0)),
                ('character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='characters.character')),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='characters.skill')),
            ],
            options={
                'unique_together': {('character', 'skill')},
            },
        ),
        migrations.AddField(
            model_name='character',
            name='skills',
            field=models.ManyToManyField(blank=True, related_name='characters', through='characters.CharacterSkill', to='characters.skill'),
        ),
    ]
