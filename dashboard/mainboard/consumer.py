from channels.generic.websocket import AsyncWebsocketConsumer
import json
import asyncio

class SensorConsumer(AsyncWebsocketConsumer):
    _qst = 0
    _dst = 0
    
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        statistics = json.loads(text_data)
        print(statistics)
        self._qst = statistics.Qst
        self._qst = statistics.Dst
        print(self._qst)
        print(self._qst)
        await self.send(text_data="Información recibida: " + text_data)