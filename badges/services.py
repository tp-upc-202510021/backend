from datetime import timezone
from jsonschema import ValidationError

from learningmodules.models import LearningModule
from learningpaths.models import LearningPath
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
    winner.friend_game_wins += 1
    winner.save()
    if winner.friend_game_wins == 1:
        user_win_first_friend_game(winner_id)
    elif winner.friend_game_wins == 3:
        user_win_thrist_friend_game(winner_id)
    elif winner.friend_game_wins == 5:
        user_win_five_friend_game(winner_id)
    winner.save()
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
    async_to_sync(channel_layer.group_send)(
        f"user_{winner_id}",
        {
            "type": "send_badge_notification",
            "event": {
                "type": "game_winner",
                "message": f"¡Felicidades {winner.username}! Has ganado la partida."
            }
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
    
def check_user_completed_all_modules(user_id: int) -> None:
    """
    Verifica si el usuario ha aprobado todos los módulos de todas sus rutas asignadas.
    Si es así, se crea el badge y se envía una notificación por WebSocket.
    """
    user_paths = LearningPath.objects.filter(user_id=user_id)

    if not user_paths.exists():
        return

    for path in user_paths:
        modules = LearningModule.objects.filter(learning_path=path)
        if not modules.exists():
            continue
        if not all(module.is_approved for module in modules):
            return  

    try:
        badge = Badge.objects.get(unlock_condition="complete_all_modules")
    except Badge.DoesNotExist:
        return

    if UserBadge.objects.filter(user_id=user_id, badge=badge).exists():
        return  

    # Crear y notificar
    user_badge = UserBadge.objects.create(
        user_id=user_id,
        badge=badge,
        description=badge.description,
        date_unlocked=timezone.now(),
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "send_badge_notification",
            "data": {
                "kind": "badge",
                "badge_id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "date_unlocked": user_badge.date_unlocked.isoformat(),
            },
        },
    )

def user_win_first_friend_game(user_id: int):
    badge = Badge.objects.get(unlock_condition="win_first_friend_game")
    if UserBadge.objects.filter(user_id=user_id, badge=badge).exists():
        return
    user_badge = create_user_badge(user_id, badge.id, "Ganó su primer juego de préstamo con un amigo.")
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
    f"user_{user_id}",
    {
        "type": "send_badge_notification",
        "data": {
            "kind": "badge",
            "badge_id": badge.id,
            "name": badge.name,
            "description": badge.description,
            "date_unlocked": user_badge.date_unlocked.isoformat(),
        },
    },
    )
def user_win_thrist_friend_game(user_id: int):
    badge = Badge.objects.get(unlock_condition="win_three_games")
    if UserBadge.objects.filter(user_id=user_id, badge=badge).exists():
        return
    user_badge = create_user_badge(user_id, badge.id, "Ganó su tercer juego de préstamo con un amigo.")
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
    f"user_{user_id}",
    {
        "type": "send_badge_notification",
        "data": {
            "kind": "badge",
            "badge_id": badge.id,
            "name": badge.name,
            "description": badge.description,
            "date_unlocked": user_badge.date_unlocked.isoformat(),
        },
    },
    )
def user_win_five_friend_game(user_id: int):
    badge = Badge.objects.get(unlock_condition="win_five_games")
    if UserBadge.objects.filter(user_id=user_id, badge=badge).exists():
        return
    user_badge = create_user_badge(user_id, badge.id, "Ganó su quinto juego de préstamo con un amigo.")
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
    f"user_{user_id}",
    {
        "type": "send_badge_notification",
        "data": {
            "kind": "badge",
            "badge_id": badge.id,
            "name": badge.name,
            "description": badge.description,
            "date_unlocked": user_badge.date_unlocked.isoformat(),
        },
    },
    )
