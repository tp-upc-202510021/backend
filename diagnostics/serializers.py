from rest_framework import serializers
from diagnostics.models import Diagnostic

class DiagnosticSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnostic
        fields = ['id', 'type', 'score', 'level', 'date_taken']
        read_only_fields = ['id', 'date_taken']