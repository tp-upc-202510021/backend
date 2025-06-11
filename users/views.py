from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from jsonschema import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.serializers import LoginSerializer
from users.serializers import RegisterSerializer
from rest_framework.permissions import AllowAny,IsAuthenticated
from .services import get_confirmed_friendships, get_pending_friend_requests_for_user, get_user_with_badges, send_friend_request, respond_to_friend_request
from django.core.exceptions import ObjectDoesNotExist

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # 🎟️ Generar tokens
            tokens = RefreshToken.for_user(user)

            return Response({
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "age": user.age,
                "preference": user.preference,
                "role": user.role,
                "access": str(tokens.access_token),
                "refresh": str(tokens)
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        receiver_id = request.data.get("receiver_id")
        try:
            friendship = send_friend_request(request.user, receiver_id)
            return Response({
                "id": friendship.id,
                "status": friendship.status,
                "receiver_id": friendship.receiver_id
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RespondFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, friendship_id):
        action = request.data.get("action")  # debe ser 'accepted' o 'rejected'
        try:
            friendship = respond_to_friend_request(request.user, friendship_id, action)
            return Response({
                "id": friendship.id,
                "status": friendship.status
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PendingFriendRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pending_requests = get_pending_friend_requests_for_user(request.user)
        data = []

        for friendship in pending_requests:
            data.append({
                "friendship_id": friendship.id,
                "requester_name": friendship.requester.name
            })

        return Response(data, status=status.HTTP_200_OK)
    
class ConfirmedFriendsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        friendships = get_confirmed_friendships(user)

        data = []
        for fs in friendships:
            friend = fs.receiver if fs.requester == user else fs.requester
            data.append({
                "friend_id": friend.id,
                "friend_name": friend.name,
                "friend_email": friend.email
            })

        return Response(data, status=status.HTTP_200_OK)
    
class CurrentUserWithBadgesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user_data = get_user_with_badges(request.user.id)
            return Response(user_data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

class UserByIdWithBadgesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user_data = get_user_with_badges(user_id)
            return Response(user_data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

