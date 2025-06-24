from django.db import models
from users.models import User
from django.utils import timezone

class Game(models.Model):
    GAME_TYPE_CHOICES = [
        ('investment', 'Investment'),
        ('loan', 'Loan'),
    ]

    id = models.AutoField(primary_key=True)
    first_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='games_as_first_user')
    second_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='games_as_second_user')
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=20, choices=GAME_TYPE_CHOICES)
    first_user_result = models.DecimalField(max_digits=10, decimal_places=2)
    second_user_result = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.get_type_display()} Game between {self.first_user} and {self.second_user}"
    

class LoanGameSession(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('active', 'Active'),
        ('rejected', 'Rejected'),
        ('finished', 'Finished')
    ]

    player_1 = models.ForeignKey(User, related_name='loan_games_as_creator', on_delete=models.CASCADE)
    player_2 = models.ForeignKey(User, related_name='loan_games_as_invited', on_delete=models.CASCADE)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    current_round = models.IntegerField(default=1)
    game_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"LoanGameSession {self.id} [{self.player_1.username} vs {self.player_2.username}]"

class LoanGameRoundResult(models.Model):
    session = models.ForeignKey('LoanGameSession', on_delete=models.CASCADE, related_name='round_results')
    round_number = models.IntegerField()

    player_1_option = models.JSONField()
    player_1_total_paid = models.DecimalField(max_digits=10, decimal_places=2)
    player_1_total_interest = models.DecimalField(max_digits=10, decimal_places=2)

    player_2_option = models.JSONField()
    player_2_total_paid = models.DecimalField(max_digits=10, decimal_places=2)
    player_2_total_interest = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'round_number')

    def __str__(self):
        return f"Resultados Ronda {self.round_number} - Juego {self.session.id}"
    

class InvestmentGameSession(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('active', 'Active'),
        ('rejected', 'Rejected'),
        ('finished', 'Finished')
    ]

    player_1 = models.ForeignKey(User, related_name='investment_games_as_creator', on_delete=models.CASCADE)
    player_2 = models.ForeignKey(User, related_name='investment_games_as_invited', on_delete=models.CASCADE)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    current_round = models.IntegerField(default=1)
    game_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"InvestmentGameSession {self.id} [{self.player_1.username} vs {self.player_2.username}]"
    



