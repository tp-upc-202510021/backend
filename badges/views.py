from django.shortcuts import render
from jsonschema import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .services import create_badge, create_user_badge, get_user_badges_by_user

class CreateBadgeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        badge = create_badge(
            name=data.get("name"),
            description=data.get("description"),
            unlock_condition=data.get("unlock_condition")
        )
        return Response({"id": badge.id}, status=status.HTTP_201_CREATED)

class CreateUserBadgeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        user = request.user
        badge_id = data.get("badge_id")
        description = data.get("description")

        try:
            user_badge = create_user_badge(
                user_id=user.id,
                badge_id=badge_id,
                description=description
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "id": user_badge.id,
            "user_id": user_badge.user_id,
            "badge_name": user_badge.badge.name
        }, status=status.HTTP_201_CREATED)

class UserBadgesByUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_badges = get_user_badges_by_user(user.id)
        data = []
        for ub in user_badges:
            data.append({
                "id": ub.id,
                "user_id": ub.user_id,
                "description": ub.description,
                "date_unlocked": ub.date_unlocked,
                "badge_name": ub.badge.name,
                "badge_description": ub.badge.description
            })
        return Response(data, status=status.HTTP_200_OK)

