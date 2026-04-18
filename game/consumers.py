import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

class WorldConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.world_id = self.scope['url_route']['kwargs']['world_id']
        self.user = self.scope['user']
        self.room_group_name = f'world_{self.world_id}'
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )
        
        await self.add_user_to_online()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user.id,
                    'username': self.user.username
                }
            )
            
            await self.remove_user_from_online()
            
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']
        
        if message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'house_update':
            await self.handle_house_update(data)
        elif message_type == 'player_move':
            await self.handle_player_move(data)

    async def handle_chat_message(self, data):
        message = data['message']
        
        await self.save_chat_message(message)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user_id': self.user.id,
                'username': self.user.username,
                'timestamp': data.get('timestamp')
            }
        )

    async def handle_house_update(self, data):
        updates = data['updates']
        
        await self.update_house_data(updates)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'house_updated',
                'updates': updates,
                'user_id': self.user.id
            }
        )

    async def handle_player_move(self, data):
        position = data['position']
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_moved',
                'user_id': self.user.id,
                'username': self.user.username,
                'position': position
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def house_updated(self, event):
        await self.send(text_data=json.dumps({
            'type': 'house_update',
            'updates': event['updates'],
            'user_id': event['user_id']
        }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username']
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username']
        }))

    async def player_moved(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_moved',
            'user_id': event['user_id'],
            'username': event['username'],
            'position': event['position']
        }))

    @database_sync_to_async
    def save_chat_message(self, message):
        from .models import RealTimeChat, World
        world = World.objects.get(id=self.world_id)
        RealTimeChat.objects.create(
            server=world,
            user=self.user,
            message=message
        )

    @database_sync_to_async
    def update_house_data(self, updates):
        from .models import PlayerHome
        pass

    @database_sync_to_async
    def add_user_to_online(self):
        pass

    @database_sync_to_async
    def remove_user_from_online(self):
        pass