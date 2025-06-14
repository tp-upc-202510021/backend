from django.shortcuts import render
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from diagnostics.serializers import DiagnosticSerializer,LearningSectionSerializer, DiagnosticQuestionSerializer
from diagnostics.services import create_diagnostic, get_diagnostics_for_user, get_all_learning_sections, get_all_diagnostic_questions
from django.core.exceptions import ObjectDoesNotExist
class DiagnosticCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DiagnosticSerializer(data=request.data)
        if serializer.is_valid():
            diagnostic = create_diagnostic(request.user, serializer.validated_data)
            output_serializer = DiagnosticSerializer(diagnostic)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class DiagnosticListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            diagnostics = get_diagnostics_for_user(request.user)
            serializer = DiagnosticSerializer(diagnostics, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "No diagnostics found for this user."},
                status=status.HTTP_404_NOT_FOUND
            )
        

class LearningSectionListView(generics.ListAPIView):
    """
    Esta vista expone una lista de todas las secciones de aprendizaje.
    La vista ahora es "delgada": su única responsabilidad es orquestar 
    la llamada al servicio y la serialización.
    """
    # El serializer no cambia.
    serializer_class = LearningSectionSerializer

    def get_queryset(self):
        """
        Sobrescribe el método base para obtener el queryset desde la capa de servicios.
        """
        return get_all_learning_sections()


# --- Vista para obtener TODAS las Preguntas de Diagnóstico ---

class DiagnosticQuestionListView(generics.ListAPIView):
    """
    Expone una lista de todas las preguntas de diagnóstico.
    Utiliza el servicio correspondiente para obtener los datos.
    """
    serializer_class = DiagnosticQuestionSerializer

    def get_queryset(self):
        """
        Llama a la función de servicio que ya contiene la lógica
        y la optimización de la consulta.
        """
        return get_all_diagnostic_questions()


