from channels.generic.websocket import AsyncWebsocketConsumer
import json

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f"user_{self.user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def game_invitation(self, event):
        await self.send(text_data=json.dumps(event))

    async def game_accepted(self, event):
        await self.send(text_data=json.dumps(event))

    async def game_rejected(self, event):
        await self.send(text_data=json.dumps(event))

    async def game_started(self, event):
        await self.send(text_data=json.dumps(event))

    async def send_badge_notification(self, event):
        await self.send(text_data=json.dumps(event["data"]))

