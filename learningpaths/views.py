from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from learningpaths.services import create_learning_path_with_modules

class CreateLearningPathView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            data = create_learning_path_with_modules(request.user)
            return Response(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


