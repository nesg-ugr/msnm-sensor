from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
import json

class SensorConsumer(AsyncWebsocketConsumer):
    _ts = []
    _qst = []
    _dst = []
    _uclq = []
    _ucld = []
    
    async def connect(self):
        self.channel_layer.group_add("sensors", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        self.channel_layer.group_discard("sensors", self.channel_name)
        await self.close()

    async def receive(self, text_data):
        statistics = json.loads(text_data)
        if len(self._ts) > 20:
            self._ts.pop(0)
            self._qst.pop(0)
            self._dst.pop(0)
            self._uclq.pop(0)
            self._ucld.pop(0)
            self._ts.append(statistics[0]['ts'])
            self._qst.append(statistics[0]['Qst'])
            self._dst.append(statistics[0]['Dst'])
            self._uclq.append(statistics[0]['UCLq'])
            self._ucld.append(statistics[0]['UCLd'])
        else:
            self._ts.append(statistics[0]['ts'])
            self._qst.append(statistics[0]['Qst'])
            self._dst.append(statistics[0]['Dst'])
            self._uclq.append(statistics[0]['UCLq'])
            self._ucld.append(statistics[0]['UCLd'])

        print(self._ts)
        print(self._qst)
        print(self._dst)
        print(self._uclq)
        print(self._ucld)
        await self.send(text_data="Information received")

    async def send_config_data(self, data):
        # Enviar datos al cliente
        await self.send(json.dumps(data))