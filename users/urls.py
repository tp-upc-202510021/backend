from django.urls import path
from users.views import ConfirmedFriendsView, LoginView, PendingFriendRequestsView, RegisterView, RespondFriendRequestView, SendFriendRequestView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('friendships/send/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('friendships/respond/<int:friendship_id>/', RespondFriendRequestView.as_view(), name='respond-friend-request'),
    path('friendships/pending/', PendingFriendRequestsView.as_view(), name='pending-friend-requests'),
    path('friends/', ConfirmedFriendsView.as_view(), name='confirmed-friends'),
]