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

    async def close(self):
        """
        Method for closing the websocket connection

        Returns:
            None

        Side effects:
            Closes the websocket connection with the dashboard
        """
        await self.websocket.close()

    async def send_statistics(self, Qst, Dst):
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
            await self.websocket.send(f"Qst: {Qst}, Dst: {Dst}")
        except Exception as e:
            raise e
