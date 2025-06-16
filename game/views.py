from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from .services import create_loan_game_investment
class LoanGameAIView(APIView):
    def get(self, request):
        result = create_loan_game_investment()
        return Response(result)