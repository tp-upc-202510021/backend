from rest_framework import serializers
from diagnostics.models import Diagnostic
from rest_framework import serializers
from .models import LearningSection, DiagnosticQuestion, AnswerOption
class DiagnosticSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnostic
        fields = ['id', 'type', 'score', 'level', 'date_taken']
        read_only_fields = ['id', 'date_taken']




class LearningSectionSerializer(serializers.ModelSerializer):
    """
    Convierte cada objeto LearningSection a formato JSON.
    Expone los campos 'id', 'title', y 'description'.
    """
    class Meta:
        model = LearningSection
        fields = ['id', 'title', 'description']



class AnswerOptionSerializer(serializers.ModelSerializer):
    """
    Serializa solo las opciones de respuesta. Está diseñado para ser usado
    de forma anidada dentro del serializer de la pregunta.
    """
    class Meta:
        model = AnswerOption

        fields = ['option_identifier', 'text', 'assigned_modules']


class DiagnosticQuestionSerializer(serializers.ModelSerializer):
    """
    Serializa cada pregunta de diagnóstico.
    La parte clave es que también renderiza una lista de todas sus respuestas
    asociadas, usando el 'AnswerOptionSerializer'.
    """

    answers = AnswerOptionSerializer(many=True, read_only=True)

    class Meta:
        model = DiagnosticQuestion
        fields = ['id', 'text', 'section_block', 'answers']