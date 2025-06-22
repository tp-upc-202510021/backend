import json
import re
from google import genai
from decouple import config
import random
from typing import Tuple, Dict
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from badges.services import notify_winner_if_applicable
from game.models import Game, LoanGameSession
from users.models import User
from users.services import get_confirmed_friendships

client = genai.Client(api_key=config("GEMINI_API_KEY"))

# Crea un caso práctico para un minijuego educativo enfocado exclusivamente en préstamos.
def create_loan_game_investment():
    loan_game_prompt= """Genera un caso práctico para un minijuego educativo enfocado exclusivamente en préstamos.
La respuesta debe ser SOLO el JSON y nada más. Usa información clara, educativa y coherente con la realidad financiera del Perú a junio 2025.

{
  "base_rate_BCRP": {
    "description": "Tasa de referencia del Banco Central de Reserva del Perú",
    "rate_type": "Tasa de Referencia",
    "value": 6.25,
    "date": "2025-06-15"
  },
  "rounds": [
    {
      "round": 1,
      "statement": "[Motivo del préstamo – contexto empresarial o personal]",
      "required_amount": [monto en soles],
      "economic_outlook_statement": "[Mensaje público del BCRP u otra fuente sobre el panorama económico (coherente con 'increase', 'decrease' o 'none')]",
      "rate_variation": {
        "direction": "[\"increase\" | \"decrease\" | \"none\"]",
        "probability": [porcentaje entre 0 y 100],
        "new_rate_percentage": [nueva TCEA total solo si direction ≠ \"none\"]   // base_rate + nuevo spread
      },
      "hidden_event": {
        "statement": "[Evento fortuito e impredecible (p. ej. sismo, crisis global)]",
        "direction": "[\"increase\" | \"decrease\"]",
        "probability": [porcentaje < 8],
        "new_rate_percentage": [TCEA total resultante]   // base_rate + spread ajustado
      },
      "options": [
        {
          "financial_entity": "[Nombre ficticio parecido a una entidad peruana]",
          "interest_rate_type": "TCEA",
          "is_variable": true,
          "spread_percentage": [valor numérico > 0],        // se sumará a base_rate_BCRP.value
          "repayment_term_months": [>= 13]
        },
        {
          "financial_entity": "[...]",
          "interest_rate_type": "TCEA",
          "is_variable": false,
          "spread_percentage": [valor numérico > 0],
          "repayment_term_months": [>= 13]
        },
        {
          "financial_entity": "[...]",
          "interest_rate_type": "TCEA",
          "is_variable": false,
          "spread_percentage": [valor numérico > 0],
          "repayment_term_months": [>= 13]
        }
      ]
    },
    {
      "round": 2,
      "...": "Idéntica estructura que el round 1"
    },
    {
      "round": 3,
      "...": "Idéntica estructura que el round 1"
    },
    {
      "round": 4,
      "...": "Idéntica estructura que el round 1"
    },
    {
      "round": 5,
      "...": "Idéntica estructura que el round 1"
    }
  ]
}
Reglas obligatorias para la IA:

financial_entity debe sonar realista pero NO ser idéntica a una entidad peruana existente.

Todas las opciones usan interest_rate_type = "TCEA".

spread_percentage es el margen que se suma a base_rate_BCRP.value para obtener la TCEA total inicial.

is_variable

true si la tasa puede cambiar; false si es fija.

Solo las opciones con is_variable: true pueden verse afectadas por rate_variation y hidden_event.

repayment_term_months debe ser ≥ 13 y realista para créditos de consumo o educativos.

rate_variation.probability debe ser coherente con economic_outlook_statement.

Ej.: “BCRP prevé estabilidad” → probabilidad < 10 %.

Ej.: “BCRP advierte presiones inflacionarias” → probabilidad mayor.

hidden_event.probability debe ser < 8 % y el enunciado describir algo inesperado.

Solo 5 rondas.

No incluyas ningún texto fuera del bloque JSON.
"""
# 1. Llamar a la API de Gemini para generar el contenido del juego
    response = client.models.generate_content(
            model="gemini-2.5-pro-preview-06-05", 
            contents=loan_game_prompt,
    )
    text = response.text

    # Extraer bloque JSON usando expresión regular (si viene entre ```json ... ```)
    json_match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_str = text.strip()

    try:
        loan_game_data = json.loads(json_str)
        return loan_game_data
    except json.JSONDecodeError as e:
        return {"error": "Error parsing JSON", "raw": json_str, "details": str(e)}
    
def evaluate_rate_events(
    base_rate: float,
    economic_statement: str,
    rate_variation: Dict,
    hidden_event: Dict
) -> Tuple[str, float, bool, bool]:
    """
    Determina qué evento ocurre.
    Devuelve:
      message, new_rate, normal_event_occurred, hidden_event_occurred
    """
    direction_main = rate_variation.get("direction", "none")
    prob_main = rate_variation.get("probability", 0) / 100.0

    if direction_main != "none" and random.random() < prob_main:
        new_rate = rate_variation["new_rate_percentage"]
        msg = f"El evento anunciado: {economic_statement}. Se cumplió"
        return msg, new_rate, True, False

    prob_hidden = hidden_event.get("probability", 0) / 100.0
    if random.random() < prob_hidden:
        new_rate = hidden_event["new_rate_percentage"]
        msg = hidden_event["statement"]
        return msg, new_rate, False, True

    # --- 3) Ningún evento ocurrió ---
    return "No hubo cambios importantes, se mantiene la tasa", base_rate, False, False

def invite_user_to_loan_game(inviter: User, invited_user_id: int) -> LoanGameSession:
    friendships = get_confirmed_friendships(inviter)
    friend_ids = [f.requester.id if f.receiver == inviter else f.receiver.id for f in friendships]
    if invited_user_id not in friend_ids:
        raise ValueError("El usuario no es tu amigo confirmado")

    invited_user = User.objects.get(id=invited_user_id)

    session = LoanGameSession.objects.create(
        player_1=inviter,
        player_2=invited_user,
        status="waiting"
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_add)(f"user_{invited_user.id}", f"user_{invited_user.id}")

    async_to_sync(channel_layer.group_send)(
        f"user_{invited_user.id}",
        {
            "type": "game.invitation",
            "message": f"{inviter.name} te ha invitado a un juego de préstamos.",
            "session_id": session.id
        }
    )

    return session

def respond_to_loan_invitation(session_id: int, user: User, response: str) -> dict:
    session = LoanGameSession.objects.get(id=session_id)

    if session.player_2 != user:
        raise PermissionError("No estás autorizado para responder esta invitación")

    if session.status != 'waiting':
        raise ValueError("Este juego ya fue aceptado o rechazado")

    channel_layer = get_channel_layer()

    if response == 'reject':
        session.status = 'rejected'
        session.save()

        async_to_sync(channel_layer.group_send)(
            f"user_{session.player_1.id}",
            {
                "type": "game.rejected",
                "message": f"{user.name} rechazó tu invitación.",
                "session_id": session.id
            }
        )
        return {"message": "Invitación rechazada"}

    elif response == 'accept':
        game_data = create_loan_game_investment()
        if "error" in game_data:
            raise ValueError("Error al generar el juego con IA")

        session.status = 'active'
        session.game_data = game_data
        session.save()

        async_to_sync(channel_layer.group_send)(
            f"user_{session.player_1.id}",
            {
                "type": "game.accepted",
                "message": f"{user.name} aceptó tu invitación.",
                "session_id": session.id,
                "game_data": game_data
            }
        )
        async_to_sync(channel_layer.group_send)(
          f"user_{session.player_2.id}",
          {
              "type": "game.started",
              "message": "Has aceptado el reto. El juego ha comenzado.",
              "session_id": session.id,
              "game_data": game_data
          }
      )
        return {
            "message": "Invitación aceptada. Juego iniciado.",
            "session_id": session.id,
            "game_data": game_data
        }

    raise ValueError("Respuesta inválida. Usa 'accept' o 'reject'")

def save_loan_game_result(player_1_id: int, player_2_id: int, player_1_total_interest: float, player_2_total_interest: float):
    try:
        player_1 = User.objects.get(id=player_1_id)
        player_2 = User.objects.get(id=player_2_id)

        game = Game.objects.create(
            first_user=player_1,
            second_user=player_2,
            type="loan",
            first_user_result=player_1_total_interest,
            second_user_result=player_2_total_interest
        )
        notify_winner_if_applicable(player_1.id, player_2.id, player_1_total_interest, player_2_total_interest)
        return game
    except User.DoesNotExist:
        raise ValueError("Uno de los usuarios no existe.")