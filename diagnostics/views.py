from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from diagnostics.serializers import DiagnosticSerializer
from diagnostics.services import create_diagnostic, get_diagnostics_for_user
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

