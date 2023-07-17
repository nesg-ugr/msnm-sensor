# -*- coding: utf-8 -*-
"""
    :mod:`API module`
    ===========================================================================
    :synopsis: API
    :author: Jaime Gallardo Mateo
    :contact: jaimegallardo@correo.ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 
"""

from fastapi import FastAPI, Request
from msnm.modules.config.configure import Configure

app = FastAPI()

@app.post("/sendConfig")
async def sendConfig(config: Request):
    # Get the configuration params and load it into a singleton pattern
    sensor_config_params = Configure()

    # Get the data from the request
    config = await config.json()

    # Set new configuration params into the singleton pattern
    sensor_config_params.config_params = config


    return {
        "status": "SUCCESS",
        "message": "Config receive successfully",
        "data": sensor_config_params.get_config(),
    }