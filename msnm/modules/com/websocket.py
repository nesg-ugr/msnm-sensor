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
    ip_address: str
        IP address of the dashboard
    port: int
        Port of the dashboard
    ----------
    """

    def __init__(self, ip_address: str, port: int):
        self.ip_address = ip_address
        self.port = port

    async def send_statistics(self, Qst, Dst):
        """
        Starting point of the websocket connection

        Raises
        ------
        CommError

        """

        try:
            async with websockets.connect(f"ws://{self.ip_address}:{self.port}") as websocket:
                await websocket.send(f"Qst: {Qst}, Dst: {Dst}")
                message = await websocket.recv()
                print(f"Received: {message}")
        except Exception as e:
            raise e
