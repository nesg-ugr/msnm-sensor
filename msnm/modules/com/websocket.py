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
        self.websocket = await websockets.connect(f"ws://{self.ip_address}:{self.port}")

    async def send_statistics(self, Qst, Dst):
        """
        Starting point of the websocket connection

        Raises
        ------
        CommError

        """

        try:
            async with self.websocket as websocket:
                await websocket.send(f"Qst: {Qst}, Dst: {Dst}")
                message = await websocket.recv()
                print(f"Received: {message}")
        except Exception as e:
            raise e
