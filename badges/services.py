from jsonschema import ValidationError
from .models import Badge, UserBadge
from users.models import User
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
def create_badge(name, description, unlock_condition):
    return Badge.objects.create(
        name=name,
        description=description,
        unlock_condition=unlock_condition
    )

def create_user_badge(user_id, badge_id, description):
    if UserBadge.objects.filter(user_id=user_id, badge_id=badge_id).exists():
        raise ValidationError("El usuario ya tiene este badge asignado.")

    user = User.objects.get(id=user_id)
    badge = Badge.objects.get(id=badge_id)

    return UserBadge.objects.create(
        user=user,
        badge=badge,
        description=description,
        date_unlocked=now()
    )

def get_user_badges_by_user(user_id):
    return UserBadge.objects.filter(user_id=user_id).select_related('badge')


def notify_winner_if_applicable(player_1_id: int, player_2_id: int, result_1: float, result_2: float):
    if result_1 == result_2:
        return 

    winner_id = player_1_id if result_1 < result_2 else player_2_id
    winner = User.objects.get(id=winner_id)

    message = {
        "type": "badge.unlocked",
        "title": "¡Felicidades!",
        "body": "Ganaste esta partida obteniendo el menor costo financiero total."
    }

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{winner_id}",
        {
            "type": "send_badge_notification",
            "event": message
        }
    )
def notify_investment_winner_if_applicable(player_1_id: int, player_2_id: int, result_1: float, result_2: float):
    if result_1 == result_2:
        return 

    winner_id = player_1_id if result_1 > result_2 else player_2_id
    winner = User.objects.get(id=winner_id)

    message = {
        "type": "badge.unlocked",
        "title": "¡Felicidades!",
        "body": "Ganaste esta partida obteniendo el mayor retorno de inversión."
    }

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{winner_id}",
        {
            "type": "send_badge_notification",
            "event": message
        }
    )

def user_win_first_step(user_id: int):
    try:
        badge = Badge.objects.get(unlock_condition="complete_first_module")
        if UserBadge.objects.filter(user_id=user_id, badge=badge).exists():
            return
        user_badge =create_user_badge(user_id, badge.id, "Completó su primer módulo exitosamente.")
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",            # mismo naming que uses al conectar
            {
                "type": "send_badge_notification",  # método que ejecutará el consumer
                "data": {
                    "kind": "badge",       # <- identificamos que es logro
                    "badge_id": badge.id,
                    "name": badge.name,
                    "description": badge.description,
                    "date_unlocked": user_badge.date_unlocked.isoformat(),
                },
            },
        )
    except ObjectDoesNotExist:
        raise ValidationError("El badge 'El primer paso' no existe.")