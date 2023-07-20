# -*- coding: utf-8 -*-
"""
    :mod:`API module`
    ===========================================================================
    :synopsis: API that allow to receive the configuration params from the dashboard
    :author: Jaime Gallardo Mateo
    :contact: jaimegallardo@correo.ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 
"""

import uvicorn
from ..config.configure import Configure
from fastapi import FastAPI, Request

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

if __name__ == '__main__':
    uvicorn.run(app,host='127.0.0.1', port=8989)