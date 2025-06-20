from django.urls import re_path
from .consumers import GameConsumer

websocket_urlpatterns = [
    re_path(r"ws/game/(?P<user_id>\d+)/$", GameConsumer.as_asgi()),
]