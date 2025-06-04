from jsonschema import ValidationError
from .models import Badge, UserBadge
from users.models import User
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist

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
