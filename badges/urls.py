from django.urls import path
from .views import CreateBadgeView, CreateUserBadgeView, UserBadgesByUserView

urlpatterns = [
    path('badges/create/', CreateBadgeView.as_view(), name='create-badge'),
    path('user-badges/create/', CreateUserBadgeView.as_view(), name='create-user-badge'),
    path('user-badges/', UserBadgesByUserView.as_view(), name='user-badges-by-authenticated-user'),
]