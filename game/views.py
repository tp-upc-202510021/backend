from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from .services import create_loan_game_investment, evaluate_rate_events, invite_user_to_loan_game, respond_to_loan_invitation
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

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
        
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def invite_to_game_view(request):
    invited_user_id = request.data.get("invited_user_id")
    if not invited_user_id:
        return Response({"error": "Falta el ID del usuario invitado"}, status=400)

    try:
        session = invite_user_to_loan_game(request.user, invited_user_id)
        return Response({
            "message": "Invitación enviada.",
            "session_id": session.id
        }, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def respond_to_game_view(request, session_id):
    response = request.data.get("response")  # "accept" o "reject"
    if response not in ["accept", "reject"]:
        return Response({"error": "Respuesta inválida. Usa 'accept' o 'reject'"}, status=400)

    try:
        result = respond_to_loan_invitation(session_id, request.user, response)
        return Response(result)
    except Exception as e:
        return Response({"error": str(e)}, status=400)