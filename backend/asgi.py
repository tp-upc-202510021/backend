# backend/asgi.py

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from game.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()  

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  
    "websocket": AuthMiddlewareStack(  
        URLRouter(websocket_urlpatterns)  
    ),
})