from django.db import models

# Create your models here.
from django.db import models
from users.models import User  

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
    
class LearningSection(models.Model):
    """
    Model to store each section of the loan learning path.
    """
    id = models.IntegerField(
        primary_key=True,
        help_text="Numeric ID that matches the section number in the learning path."
    )
    
    title = models.CharField(
        max_length=255,
        help_text="The title of the learning section."
    )
    
    description = models.TextField(
        help_text="The full description of the section. Supports long text, paragraphs, and special characters for formulas."
    )
    def __str__(self):
        return f"{self.id}. {self.title}"

class DiagnosticQuestion(models.Model):
    """
    Almacena una pregunta del cuestionario de diagnóstico.
    """
    id = models.IntegerField(
        primary_key=True,
        help_text="ID numérico de la pregunta (ej: 1, 2, 3...)"
    )
    text = models.TextField(
        help_text="El texto completo de la pregunta."
    )
    section_block = models.CharField(
        max_length=10,
        help_text="El bloque de secciones que cubre esta pregunta (ej: '1-4')."
    )

    class Meta:
        verbose_name = "Diagnostic Question"
        verbose_name_plural = "Diagnostic Questions"
        ordering = ['id']

    def __str__(self):
        return f"Q{self.id}: {self.text[:50]}..."


class AnswerOption(models.Model):
    """
    Almacena una opción de respuesta para una pregunta de diagnóstico.
    Cada pregunta tendrá varias de estas (a, b, c, d).
    """
    question = models.ForeignKey(
        DiagnosticQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        help_text="La pregunta a la que pertenece esta respuesta."
    )
    option_identifier = models.CharField(
        max_length=1,
        help_text="El identificador de la opción (ej: 'a', 'b', 'c', 'd')."
    )
    text = models.TextField(
        help_text="El texto completo de la opción de respuesta."
    )
    assigned_modules = models.JSONField(
        default=list,
        help_text="Una lista JSON de los IDs de los módulos a asignar si se elige esta respuesta."
    )

    class Meta:
        unique_together = ('question', 'option_identifier')
        ordering = ['question', 'option_identifier']

    def __str__(self):
        return f"Answer '{self.option_identifier}' for Question {self.question.id}"
