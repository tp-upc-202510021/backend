from django.db import models
from users.models import User

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

