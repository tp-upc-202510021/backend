from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from .services import create_loan_game_investment, evaluate_rate_events
from rest_framework import status


class LoanGameAIView(APIView):
    def get(self, request):
        result = create_loan_game_investment()
        return Response(result)
    
class RateEventView(APIView):
    """
    POST /api/rate-event/
    Body JSON:
    {
      "base_rate": 6.25,
      "economic_outlook_statement": "...",
      "rate_variation": {...},
      "hidden_event": {...}
    }
    """
    def post(self, request):
        try:
            data = request.data
            base_rate = float(data["base_rate"])
            econ_statement = data["economic_outlook_statement"]
            rate_variation = data["rate_variation"]
            hidden_event = data["hidden_event"]

            msg, new_rate, normal_occurred, hidden_occurred = evaluate_rate_events(
                base_rate, econ_statement, rate_variation, hidden_event
            )

            return Response(
                {
                    "message": msg,
                    "original_rate": base_rate,
                    "new_rate": new_rate,
                    "normal_event_occurred": normal_occurred,
                    "hidden_event_occurred": hidden_occurred
                },
                status=status.HTTP_200_OK
            )
        except (KeyError, ValueError) as exc:
            return Response(
                {"error": f"Invalid input: {exc}"},
                status=status.HTTP_400_BAD_REQUEST
            )