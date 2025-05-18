from django.db import models

# Create your models here.
from django.db import models
from users.models import User  # Importa tu modelo personalizado

class Diagnostic(models.Model):
    TYPE_CHOICES = [
        ('loans', 'Loans'),
        ('investments', 'Investments'),
    ]

    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diagnostics')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    score = models.PositiveIntegerField()
    level = models.TextField()
    date_taken = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diagnostic for {self.user.email} - {self.type} ({self.level})"
