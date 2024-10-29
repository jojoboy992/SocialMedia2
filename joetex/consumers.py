# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message
from django.contrib.auth.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.username = self.scope["url_route"]["kwargs"]["username"]
        self.room_group_name = f"chat_{self.username}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Load previous messages (optional)
        previous_messages = await database_sync_to_async(self.load_previous_messages)()
        for message in previous_messages:
            await self.send(
                text_data=json.dumps(
                    {
                        "message": message.content,
                        "sender": message.sender.username,  # Assuming you have a sender field in Message
                    }
                )
            )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        # Save the message to the database
        await database_sync_to_async(self.save_message)(message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": self.scope["user"].username,  # Get the username of the sender
            },
        )

    async def chat_message(self, event):
        message = event["message"]
        sender = event["sender"]

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "sender": sender,  # Include sender information for display
                }
            )
        )

    @database_sync_to_async
    def load_previous_messages(self):
        # Load previous messages for the current user and the chat partner
        return Message.objects.filter(
            sender=self.scope["user"], receiver__username=self.username
        )

    @database_sync_to_async
    def save_message(self, message_content):
        # Save a new message to the database
        Message.objects.create(
            sender=self.scope["user"],
            receiver=User.objects.get(username=self.username),
            content=message_content,
        )
