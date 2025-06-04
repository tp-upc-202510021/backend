from django.db import models
from users.models import User  # Ajusta el import si tu modelo se llama diferente
class Badge(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    unlock_condition = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    description = models.CharField(max_length=50)
    date_unlocked = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'badge')  
        verbose_name = "User Badge"
        verbose_name_plural = "User Badges"

    def __str__(self):
        return f"{self.user.email} - {self.badge.name}"
