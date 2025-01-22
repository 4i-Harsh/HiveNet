import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.friend_id = self.scope['url_route']['kwargs']['friend_id']
        
        # Create a unique room name using sorted user IDs
        room_users = sorted([self.user.id, int(self.friend_id)])
        self.room_name = f"chat_{room_users[0]}_{room_users[1]}"
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        receiver_id = text_data_json['receiver_id']

        # Save message to database
        saved_message = await self.save_message(message, receiver_id)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': {
                    'content': message,
                    'sender_id': self.user.id,
                    'timestamp': saved_message.timestamp.isoformat()
                }
            }
        )

    async def chat_message(self, event):
        message = event['message']
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    @database_sync_to_async
    def save_message(self, content, receiver_id):
        receiver = User.objects.get(id=receiver_id)
        return ChatMessage.objects.create(
            sender=self.user,
            receiver=receiver,
            content=content
        ) 