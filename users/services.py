from .models import UserFriendship, User
from django.core.exceptions import ValidationError
from django.db.models import Q
from badges.models import UserBadge

def send_friend_request(requester, receiver_id):
    if requester.id == receiver_id:
        raise ValidationError("No puedes enviarte una solicitud de amistad a ti mismo.")

    if UserFriendship.objects.filter(requester=requester, receiver_id=receiver_id).exists():
        raise ValidationError("Ya enviaste una solicitud a este usuario.")

    receiver = User.objects.get(id=receiver_id)
    friendship = UserFriendship.objects.create(
        requester=requester,
        receiver=receiver,
        status='pending'
    )
    return friendship

def respond_to_friend_request(receiver, friendship_id, action):
    try:
        friendship = UserFriendship.objects.get(id=friendship_id, receiver=receiver)
    except UserFriendship.DoesNotExist:
        raise ValidationError("No tienes permiso para responder a esta solicitud.")

    if friendship.status != 'pending':
        raise ValidationError("Esta solicitud ya ha sido respondida.")

    if action not in ['accepted', 'rejected']:
        raise ValidationError("Acción inválida. Usa 'accepted' o 'rejected'.")

    friendship.status = action
    friendship.save()
    return friendship

def get_pending_friend_requests_for_user(user):
    return UserFriendship.objects.filter(
        receiver=user,
        status='pending'
    ).select_related('requester')

def get_confirmed_friendships(user):
    friendships = UserFriendship.objects.filter(
        status='accepted'
    ).filter(
        Q(requester=user) | Q(receiver=user)
    ).select_related('requester', 'receiver')

    return friendships


def get_user_with_badges(user_id):
    user = User.objects.get(id=user_id)
    badges = UserBadge.objects.filter(user=user).select_related('badge')

    badge_list = [
        {
            "badge_id": ub.badge.id,
            "name": ub.badge.name,
            "description": ub.badge.description,
            "unlock_condition": ub.badge.unlock_condition,
            "user_description": ub.description,
            "date_unlocked": ub.date_unlocked
        }
        for ub in badges
    ]

    user_data = {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "age": user.age,
        "preference": user.preference,
        "role": user.role,
        "date_joined": user.date_joined,
        "badges": badge_list
    }

    return user_data

