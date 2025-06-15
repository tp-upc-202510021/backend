from diagnostics.models import Diagnostic
from django.core.exceptions import ObjectDoesNotExist
from .models import Diagnostic
from typing import Dict, Any
from users.models import User
def create_diagnostic(user, validated_data):
    
    if Diagnostic.objects.filter(user=user).exists():
        raise ValueError("Ya existe un diagnóstico para este usuario.")
    diagnostic = Diagnostic.objects.create(
        user=user,
        type=validated_data['type'],
        score=validated_data['score'],
        level=validated_data['level'],
    )
    return diagnostic

def get_diagnostics_for_user(user):
    diagnostics = Diagnostic.objects.filter(user=user)
    if not diagnostics.exists():
        raise ObjectDoesNotExist("No diagnostics found for this user.")
    return diagnostics
def get_user_level(user_id):
    try:
        diagnostic = Diagnostic.objects.filter(user_id=user_id).order_by('-date_taken').first()
        if diagnostic:
            return diagnostic.level
        return None
    except Diagnostic.DoesNotExist:
        return None
    
from .models import LearningSection, DiagnosticQuestion

def get_all_learning_sections():
    """
    Retorna un queryset con todas las secciones de aprendizaje.
    """
    return LearningSection.objects.all()

def get_all_diagnostic_questions():
    """
    Retorna un queryset con todas las preguntas de diagnóstico.
    Incluye una optimización de rendimiento para precargar las respuestas anidadas.
    """
    return DiagnosticQuestion.objects.prefetch_related('answers').all()

def create_diagnostic(*, user: User, data: Dict[str, Any]) -> Diagnostic:

    diagnostic_obj = Diagnostic.objects.create(
        user=user,
        type=user.preference,
        **data
    )
    
    return diagnostic_obj