from channels.generic.websocket import AsyncWebsocketConsumer
import json

class SensorConsumer(AsyncWebsocketConsumer):
    _ts = []
    _qst = []
    _dst = []
    
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        statistics = json.loads(text_data)
        if len(self._ts) > 10:
            self._ts.pop(0)
            self._ts.append(statistics[0]['ts'])
        else:
            self._ts.append(statistics[0]['ts'])

        if len(self._qst) > 10:
            self._qst.pop(0)
            self._qst.append(statistics[0]['Qst'])
        else:
            self._qst.append(statistics[0]['Qst'])
        
        if len(self._dst) > 10:
            self._dst.pop(0)
            self._dst.append(statistics[0]['Dst'])
        else:
            self._dst.append(statistics[0]['Dst'])

        print(self._ts)
        print(self._qst)
        print(self._dst)
        await self.send(text_data="Information received")