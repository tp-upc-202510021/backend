from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from diagnostics.serializers import DiagnosticSerializer
from diagnostics.services import create_diagnostic

class DiagnosticCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DiagnosticSerializer(data=request.data)
        if serializer.is_valid():
            diagnostic = create_diagnostic(request.user, serializer.validated_data)
            output_serializer = DiagnosticSerializer(diagnostic)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

