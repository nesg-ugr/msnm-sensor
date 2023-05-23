import json
from channels.generic.websocket import AsyncWebsocketConsumer

class SensorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        await self.send(text_data="Información recibida: " + text_data)