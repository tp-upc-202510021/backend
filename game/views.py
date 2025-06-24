from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from .services import apply_exchange_event, create_loan_game_investment, evaluate_rate_events, generate_investment_game, invite_user_to_investment_game, invite_user_to_loan_game, respond_to_investment_invitation, respond_to_loan_invitation, save_loan_game_result
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

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

@method_decorator(csrf_exempt, name='dispatch')
class RespondToGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get("session_id")
        response = request.data.get("response")  # "accept" o "reject"

        if not session_id or response not in ["accept", "reject"]:
            return Response({"error": "Faltan datos o la respuesta es inválida."}, status=400)

        try:
            result = respond_to_loan_invitation(session_id, request.user, response)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        
class SaveLoanGameResultView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        player_1_id = data.get("player_1_id")
        player_2_id = data.get("player_2_id")
        player_1_result = data.get("player_1_total_interest")
        player_2_result = data.get("player_2_total_interest")
        print("player_1_id:", player_1_id)
        print("player_2_id:", player_2_id)
        print("player_1_total_interest:", player_1_result)
        print("player_2_total_interest:", player_2_result)
        if any(v is None for v in [player_1_id, player_2_id, player_1_result, player_2_result]):
            return Response({"error": "Faltan datos obligatorios"}, status=400)

        try:
            game = save_loan_game_result(
                int(player_1_id),
                int(player_2_id),
                float(player_1_result),
                float(player_2_result)
            )
            return Response({
                "message": "Resultado guardado correctamente",
                "game_id": game.id,
                "first_user": game.first_user.name,
                "second_user": game.second_user.name,
                "first_user_result": float(game.first_user_result),
                "second_user_result": float(game.second_user_result)
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
class ExchangeEventView(APIView):
    """
    Recibe la configuración de la variación cambiaria enviada por el frontend
    y devuelve la respuesta generada por el servicio `apply_exchange_event`.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        required_fields = [
            "current_change_to_buy",
            "current_change_to_sell",
            "probability_to_change",
            "type_of_change",
            "percentage_of_variation",
            "event"
        ]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return Response(
                {"detail": f"Faltan campos requeridos: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            base_buy = float(data["current_change_to_buy"])
            base_sell = float(data["current_change_to_sell"])
            probability = int(data["probability_to_change"])
            change_type = str(data["type_of_change"]).lower()
            variation_pct = float(data["percentage_of_variation"])
            event_name = str(data["event"])
        except (ValueError, TypeError):
            return Response(
                {"detail": "Tipos de dato inválidos en la carga útil."},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = apply_exchange_event(
            base_buy=base_buy,
            base_sell=base_sell,
            probability=probability,
            change_type=change_type,
            variation_pct=variation_pct,
            event_name=event_name,
        )

        return Response(result, status=status.HTTP_200_OK)
    
class InvestmentGameAIView(APIView):
    def get(self, request):
        result = generate_investment_game()
        return Response(result)
    
class InviteUserToInvestmentGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        invited_user_id = request.data.get("invited_user_id")
        if not invited_user_id:
            return Response({"error": "Falta el ID del usuario invitado"}, status=400)

        try:
            session = invite_user_to_investment_game(request.user, invited_user_id)
            return Response({
                "message": "Invitación enviada.",
                "session_id": session.id
            }, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        
class RespondToInvestmentGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get("session_id")
        response = request.data.get("response")  # "accept" o "reject"

        if not session_id or response not in ["accept", "reject"]:
            return Response({"error": "Faltan datos o la respuesta es inválida."}, status=400)

        try:
            result = respond_to_investment_invitation(session_id, request.user, response)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=400)