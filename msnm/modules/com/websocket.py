# -*- coding: utf-8 -*-
"""
    :mod:`Websocket module`
    ===========================================================================
    :synopsis: Websocket client
    :author: Jaime Gallardo Mateo
    :contact: jaimegallardo@correo.ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 
"""

import asyncio
import websockets
import json
from datetime import datetime


class Websocket:
    """
    *MSNM Websocket client module*. It contains the corresponding functionalities for connecting to the dashboard by websocket.

    Attributes
    ----------
    ip_address
        IP address of the dashboard
    port
        Port of the dashboard
    ----------
    """

    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port
        self.websocket = None

    async def connect(self):
        """
        Method for connecting to the dashboard by websocket

        Returns:
            None

        Side effects:
            Establishes a websocket connection with the dashboard
        """
        self.websocket = await websockets.connect(f"ws://{self.ip_address}:{self.port}/ws/monitoring/", ping_timeout=40)

    async def close(self):
        """
        Method for closing the websocket connection

        Returns:
            None

        Side effects:
            Closes the websocket connection with the dashboard
        """
        await self.websocket.close()

    async def send_statistics(self, ts, Qst, Dst, UCLq, UCLd):
        """
        Method for sending statistics to the dashboard

        Parameters
        ----------
        Qst

        Dst
        -------

        Raises
        ------
        Exception
        """

        try:
            await self.websocket.send(json.dumps([{'ts':ts,'Qst':Qst,'Dst':Dst,'UCLq':UCLq,'UCLd':UCLd}]))
        except Exception as e:
            raise e

    async def receive(self):
        """
        Method for receiving messages from the dashboard

        Returns:
            Message received from the dashboard
        """
        data = await self.websocket.recv()
        print(data)
        return data