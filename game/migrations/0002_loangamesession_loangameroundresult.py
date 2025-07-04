# Generated by Django 5.2 on 2025-06-20 06:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LoanGameSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('waiting', 'Waiting'), ('active', 'Active'), ('rejected', 'Rejected'), ('finished', 'Finished')], default='waiting', max_length=20)),
                ('current_round', models.IntegerField(default=1)),
                ('game_data', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('player_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loan_games_as_creator', to=settings.AUTH_USER_MODEL)),
                ('player_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loan_games_as_invited', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LoanGameRoundResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round_number', models.IntegerField()),
                ('player_1_option', models.JSONField()),
                ('player_1_total_paid', models.DecimalField(decimal_places=2, max_digits=10)),
                ('player_1_total_interest', models.DecimalField(decimal_places=2, max_digits=10)),
                ('player_2_option', models.JSONField()),
                ('player_2_total_paid', models.DecimalField(decimal_places=2, max_digits=10)),
                ('player_2_total_interest', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='round_results', to='game.loangamesession')),
            ],
            options={
                'unique_together': {('session', 'round_number')},
            },
        ),
    ]
