from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .services import create_quiz_result, generate_quizzes_from_gemini, get_latest_quiz_with_questions_and_answers

class GenerateQuizView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, module_id):
        try:
            quiz = generate_quizzes_from_gemini(module_id)
            return Response({
                "quiz_id": quiz.id,
                "module_id": quiz.module_id,
                "total_questions": quiz.total_questions
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LatestQuizView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, module_id):
        try:
            data = get_latest_quiz_with_questions_and_answers(module_id)
            return Response(data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
class CreateQuizResultView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        quiz_id = data.get("quiz_id")
        score = data.get("score")

        if quiz_id is None or score is None:
            return Response({"detail": "quiz_id y score son requeridos."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result_data = create_quiz_result(request.user, quiz_id, score)
            return Response(result_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
