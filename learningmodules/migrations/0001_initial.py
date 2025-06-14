# Generated by Django 5.2 on 2025-05-31 22:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('learningpaths', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('type', models.CharField(max_length=20)),
                ('level', models.CharField(max_length=20)),
                ('order_index', models.PositiveIntegerField()),
                ('content', models.TextField(blank=True, null=True)),
                ('learning_path', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modules', to='learningpaths.learningpath')),
            ],
            options={
                'ordering': ['order_index'],
            },
        ),
    ]
