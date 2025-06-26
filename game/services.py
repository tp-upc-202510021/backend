from decimal import Decimal, ROUND_HALF_UP 
import json
import re
from google import genai
from decouple import config
import random
from typing import Tuple, Dict
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from badges.services import notify_investment_winner_if_applicable, notify_winner_if_applicable
from game.models import Game, InvestmentGameSession, LoanGameSession
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
            "session_id": session.id,
            "game_type": "loan"
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
                "session_id": session.id,
                "game_type": "loan"
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
                "game_data": game_data,
                "game_type": "loan"
            }
        )
        async_to_sync(channel_layer.group_send)(
          f"user_{session.player_2.id}",
          {
              "type": "game.started",
              "message": "Has aceptado el reto. El juego ha comenzado.",
              "session_id": session.id,
              "game_data": game_data,
              "game_type": "loan"
          }
      )
        return {
            "message": "Invitación aceptada. Juego iniciado.",
            "session_id": session.id,
            "game_data": game_data,
            "game_type": "loan"
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
    
def apply_exchange_event(base_buy: float,
                         base_sell: float,
                         probability: int,
                         change_type: str,
                         variation_pct: float,
                         event_name: str) -> dict:
    """
    Calcula la ocurrencia y efecto de un evento cambiario.

    Args:
        base_buy: TC compra inicial.
        base_sell: TC venta inicial.
        probability: 0-100 (%).
        change_type: "positive" | "negative".
        variation_pct: porcentaje de variación.
        event_name: descripción narrativa.

    Returns:
        dict listo para serializar a JSON.
    """
    occurred = random.uniform(0, 100) < probability

    response = {
        "base_rate": {
            "buy": base_buy,
            "sell": base_sell
        },
        "event": {
            "occurred": occurred,
            "description": event_name,
            "type": change_type,
            "variation_pct": variation_pct
        }
    }

    if occurred:
        sign = 1 if change_type == "positive" else -1
        factor = 1 + sign * (variation_pct / 100)

        new_buy = Decimal(base_buy * factor).quantize(Decimal("0.001"),
                                                      rounding=ROUND_HALF_UP)
        new_sell = Decimal(base_sell * factor).quantize(Decimal("0.0001"),
                                                        rounding=ROUND_HALF_UP)

        response["event"]["new_rate"] = {
            "buy": float(new_buy),
            "sell": float(new_sell)
        }

    return response

def generate_investment_game():
    """
    Crea un caso práctico para un minijuego educativo enfocado en el tipo de cambio.
    Devuelve un diccionario con la estructura del juego.
    """
    investment_game_prompt = """Genera un caso práctico para un minijuego educativo enfocado exclusivamente en **inversiones**.  
La respuesta debe ser **SOLO el JSON y nada más**. Usa información clara, educativa y coherente con la realidad financiera del Perú a junio 2025.

Estructura y significado de cada campo
-------------------------------------

1. `initial_capital_pen`  
   • Decimal (> 0) con dos decimales.  
   • Capital inicial del jugador en soles.

2. `base_fx_rate`  
   • Objeto con dos claves:  
     – `buy`  → tipo de cambio compra PEN→USD (decimales).  
     – `sell` → tipo de cambio venta PEN→USD (decimales, siempre < `buy`).  
   • Punto de partida; se ajusta con los eventos de cada ronda.

3. `rounds`  
   • Arreglo de **exactamente 5** objetos, cada uno con:

   a. `round`  
      – Entero del 1 al 5 que identifica la ronda.  

   b. `investment_duration_months`  
      – Entero positivo (12, 18, 24, 36 …).  
      – Todas las frecuencias de las opciones DEBEN dividir este valor sin residuo.

   c. `options` (exactamente 3 por ronda)  
      • `title`               → Nombre de la opción.  
      • `description`         → Texto breve y pedagógico.  
      • `expected_return_pct` → Decimal > 0 (rentabilidad anual base en %).  
      • `volatility_pct`      → Decimal 0–100 (sensibilidad a eventos en %).  
      • `risk_level`          → `"LOW"` | `"MEDIUM"` | `"HIGH"`.  
      • `frequency`           → `"ANNUAL"` (12 m) | `"SEMI_ANNUAL"` (6 m) | `"QUARTERLY"` (3 m) | `"MONTHLY"` (1 m).  
                               *Debe dividir exactamente `investment_duration_months`.*  
      • `currency`            → `"PEN"` | `"USD"`.

   d. `fx_event`  
      • `probability_to_change`   → Entero 0–100 (probabilidad de que ocurra).  
      • `type_of_change`          → `"positive"` (sube el USD) | `"negative"` (baja el USD).  
      • `percentage_of_variation` → Decimal > 0 (magnitud absoluta en %).  
      • `event_description`       → Cadena coherente con `type_of_change` y la coyuntura peruana.  
      • **No incluyas** valores actuales de compra/venta aquí; se calculan a partir de `base_fx_rate`.

Reglas obligatorias
-------------------

* Solo 5 rondas.  
* `options` debe contener exactamente 3 elementos.  
* Las frecuencias de cada opción deben ser divisores exactos de `investment_duration_months`.  
* `volatility_pct` y `risk_level` deben ser coherentes con `expected_return_pct`.  
* El JSON **no debe** incluir comentarios ni ningún texto explicativo fuera del objeto.

Ejemplo de referencia (con marcadores – NO incluyas comentarios en la salida)
-----------------------------------------------------------------------------

```jsonc
{
  "initial_capital_pen": 12000.00,
  "base_fx_rate": {
    "buy": 3.87,
    "sell": 3.84
  },
  "rounds": [
    {
      "round": 1,
      "investment_duration_months": 12,
      "options": [
        {
          "title": "Depósito a Plazo 12 m",
          "description": "Tasa fija garantizada durante 1 año.",
          "expected_return_pct": 4.5,
          "volatility_pct": 5,
          "risk_level": "LOW",
          "frequency": "ANNUAL",
          "currency": "PEN"
        },
        {
          "title": "Fondo Mutuo Mixto",
          "description": "40 % bonos y 60 % acciones.",
          "expected_return_pct": 8,
          "volatility_pct": 25,
          "risk_level": "MEDIUM",
          "frequency": "MONTHLY",
          "currency": "PEN"
        },
        {
          "title": "Acción AAPL tokenizada",
          "description": "Participación fraccionada en Apple.",
          "expected_return_pct": 14,
          "volatility_pct": 40,
          "risk_level": "HIGH",
          "frequency": "QUARTERLY",
          "currency": "USD"
        }
      ],
      "fx_event": {
        "probability_to_change": 26,
        "type_of_change": "positive",
        "percentage_of_variation": 2,
        "event_description": "Salida de capitales extranjeros"
      }
    }
    // … repetir estructura hasta round 5
  ]
} """
    # 1. Llamar a la API de Gemini para generar el contenido del juego
    response = client.models.generate_content(
            model="gemini-2.5-pro-preview-06-05", 
            contents=investment_game_prompt,
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
    
def invite_user_to_investment_game(inviter: User, invited_user_id: int) :
    friendships = get_confirmed_friendships(inviter)
    friend_ids = [f.requester.id if f.receiver == inviter else f.receiver.id for f in friendships]
    if invited_user_id not in friend_ids:
        raise ValueError("El usuario no es tu amigo confirmado")

    invited_user = User.objects.get(id=invited_user_id)

    session = InvestmentGameSession.objects.create(
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
            "message": f"{inviter.name} te ha invitado a un juego de inversiones.",
            "session_id": session.id,
            "game_type": "investment"
        }
    )

    return session
def respond_to_investment_invitation(session_id: int, user: User, response: str) -> dict:
    session = InvestmentGameSession.objects.get(id=session_id)

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
                "session_id": session.id,
                "game_type": "investment"
            }
        )
        return {"message": "Invitación rechazada"}

    elif response == 'accept':
        game_data = generate_investment_game()
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
                "game_data": game_data,
                "game_type": "investment"
            }
        )
        async_to_sync(channel_layer.group_send)(
          f"user_{session.player_2.id}",
          {
              "type": "game.started",
              "message": "Has aceptado el reto. El juego ha comenzado.",
              "session_id": session.id,
              "game_data": game_data,
              "game_type": "investment"
          }
      )
        return {
            "message": "Invitación aceptada. Juego iniciado.",
            "session_id": session.id,
            "game_data": game_data,
            "game_type": "investment"
        }

    raise ValueError("Respuesta inválida. Usa 'accept' o 'reject'")

def save_investment_game_result(player_1_id: int, player_2_id: int, player_1_total_return: float, player_2_total_return: float):
    try:
        player_1 = User.objects.get(id=player_1_id)
        player_2 = User.objects.get(id=player_2_id)

        game = Game.objects.create(
            first_user=player_1,
            second_user=player_2,
            type="investment",
            first_user_result=player_1_total_return,
            second_user_result=player_2_total_return
        )
        notify_investment_winner_if_applicable(player_1.id, player_2.id, player_1_total_return, player_2_total_return)
        return game
    except User.DoesNotExist:
        raise ValueError("Uno de los usuarios no existe.")